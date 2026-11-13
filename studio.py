"""Gemini + Edge TTS + Pillow + FFmpeg: 15 saniyelik bilgi videosu."""
import argparse
import array
import asyncio
import json
import math
import os
from pathlib import Path
import re
import subprocess
import wave

OUT = Path('output')
DURATIONS = [2.0, 9.0, 4.0]
W, H, FPS = 1080, 1920, 30


def cmd(*args):
    subprocess.run([str(a) for a in args], check=True)


def clean_plan(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get('title'), str) or not isinstance(plan.get('description'), str):
        raise ValueError('Plan başlık ve açıklama içermeli')
    scenes = plan.get('scenes')
    if not isinstance(scenes, list) or len(scenes) != 3:
        raise ValueError('Plan tam üç sahne içermeli')
    for s in scenes:
        if not isinstance(s, dict) or not all(isinstance(s.get(k), str) and s[k].strip() for k in ('narration', 'image_prompt')):
            raise ValueError('Her sahnede narration ve image_prompt olmalı')
    return plan


def fit_rate(seconds, target):
    rate = max(1.0, seconds / (target - 0.1))
    if rate > 2.5:
        raise ValueError('Ses sahneye sığmıyor; daha kısa bir senaryo gerekiyor')
    return rate


def srt_time(t):
    ms = max(0, round(t * 1000))
    h, rem = divmod(ms, 3600000); m, rem = divmod(rem, 60000); s, ms = divmod(rem, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def ass_time(t):
    cs = max(0, round(t * 100)); h, rem = divmod(cs, 360000); m, rem = divmod(rem, 6000); s, cs = divmod(rem, 100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'


def ass_escape(s):
    return str(s).replace('\\', ' ').replace('{', '').replace('}', '').replace('\n', ' ')


def plan_scenes(fact):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    model = os.environ.get('TEXT_MODEL', 'gemini-2.5-flash')
    old = json.loads(Path('history.json').read_text(encoding='utf8')) if Path('history.json').exists() else []
    prompt = ('Türkçe bir genel kültür Shorts videosu için araştırma yap. '
      'İddiaları güvenilir kaynaklarla ara, spekülasyon ve sağlık/finans tavsiyesinden kaçın. '
      'Kısa ve çocuklara uygun tek somut bilgi, doğrulama özeti ve kaynakları ver. '
      'Yakın zamanda kullanılan başlıkları tekrarlama: ' + json.dumps(old[-40:], ensure_ascii=False) + '\n' +
      ('Kullanıcının bilgisi/konusu: ' + fact if fact else 'Yeni ve şaşırtıcı bir genel kültür konusu seç.'))
    r = client.models.generate_content(model=model, contents=prompt,
          config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]))
    if not r.text or not r.candidates:
        raise RuntimeError('Araştırma yanıtı boş')
    metadata = r.candidates[0].grounding_metadata
    sources = []
    for chunk in (getattr(metadata, 'grounding_chunks', None) or []):
        web = getattr(chunk, 'web', None)
        if web and getattr(web, 'uri', None):
            s = {'title': getattr(web, 'title', '') or 'Kaynak', 'url': web.uri}
            if s['url'] not in [x['url'] for x in sources]: sources.append(s)
    if not sources:
        raise RuntimeError('Google Search kaynak sağlamadı; doğrulanmamış otomatik üretim durduruldu')
    (OUT/'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf8')
    script_prompt = ("Aşağıdaki araştırmadan Türkçe, üç sahneli 15 saniyelik Shorts planı hazırla. "
      "Yalnız JSON üret: {\"title\": string, \"description\": string, \"scenes\": "
      "[{\"narration\": string, \"image_prompt\": string}, ...]}. "
      "Tam 3 sahne: 1) 2 saniye kanca, en fazla 4 kelime; 2) 9 saniye açıklama, en fazla 16 kelime; "
      "3) 4 saniye kapanış, en fazla 7 kelime. Gerçekleri çarpıtma, kaynakta desteklenmeyen iddia ekleme. "
      "image_prompt İngilizce: aynı 3D çizgi film estetiği, dikey kompozisyon, yazı ve logo yok. "
      "Araştırma:\n" + r.text[:15000])
    response = client.models.generate_content(model=model, contents=script_prompt,
             config=types.GenerateContentConfig(response_mime_type='application/json'))
    plan = clean_plan(json.loads(response.text))
    (OUT/'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf8')
    return client, plan


def generate_image(client, scene, i):
    from PIL import Image, ImageOps
    from io import BytesIO
    prompt = ('Create one vertical 9:16 3D cartoon style illustration for a Turkish educational short. '
              'Colorful cinematic lighting, coherent art direction, no text, no letters, no watermark. '
              + scene['image_prompt'])
    model = os.environ.get('IMAGE_MODEL', 'gemini-2.5-flash-image')
    response = client.models.generate_content(model=model, contents=prompt)
    for part in (getattr(response, 'parts', None) or []):
        data = getattr(part, 'inline_data', None)
        if data and data.data:
            image = Image.open(BytesIO(data.data)).convert('RGB')
            ImageOps.fit(image, (W, H), method=Image.Resampling.LANCZOS).save(OUT/f'image{i}.png')
            return
    raise RuntimeError(f'{i}. sahne için görsel üretilmedi; model/kota/erişimi kontrol et')


async def tts(text, path):
    import edge_tts
    boundaries = []
    communicate = edge_tts.Communicate(text, voice='tr-TR-AhmetNeural', boundary='WordBoundary')
    with path.open('wb') as f:
        async for item in communicate.stream():
            if item['type'] == 'audio': f.write(item['data'])
            elif item['type'] == 'WordBoundary':
                boundaries.append((item['offset']/10000000, item['duration']/10000000, item['text']))
    if not path.stat().st_size or not boundaries:
        raise RuntimeError('TTS ses veya kelime zamanlaması döndürmedi')
    return boundaries


def media_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)], check=True, capture_output=True, text=True)
    return float(r.stdout.strip())


def make_audio_and_captions(plan):
    entries = []
    starts = [0, DURATIONS[0], DURATIONS[0] + DURATIONS[1]]
    for i, scene in enumerate(plan['scenes']):
        mp3 = OUT/f'voice{i}.mp3'
        boundaries = asyncio.run(tts(scene['narration'], mp3))
        rate = fit_rate(media_duration(mp3), DURATIONS[i])
        # atempo zincirinde her değer 0.5-2.0 aralığında kalır.
        filt = ('atempo=2,atempo='+str(rate/2) if rate > 2 else 'atempo='+str(rate))
        cmd('ffmpeg', '-v', 'error', '-y', '-i', mp3, '-af', filt+',apad', '-t', str(DURATIONS[i]), '-ar', '44100', '-ac', '1', OUT/f'voice{i}.wav')
        for start, duration, word in boundaries:
            a = starts[i]+start/rate
            b = min(starts[i]+DURATIONS[i]-0.02, starts[i]+(start+duration)/rate)
            if b > a: entries.append((a, b, word))
    (OUT/'captions.srt').write_text('\n\n'.join(f'{n}\n{srt_time(a)} --> {srt_time(b)}\n{w}' for n,(a,b,w) in enumerate(entries,1))+'\n', encoding='utf8')
    header = '''[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,82,&H00FFFFFF,&H000000FF,&H00100804,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,80,80,250,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
    lines = [f'Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,{ass_escape(w)}' for a,b,w in entries]
    (OUT/'captions.ass').write_text(header+'\n'.join(lines)+'\n', encoding='utf8')


def music():
    # Orijinal basit sentezlenmiş melodi ve iki kısa geçiş sinyali.
    sample_rate = 44100
    notes = [261.63, 329.63, 392, 329.63, 293.66, 349.23, 440, 349.23]
    pcm = array.array('h')
    for n in range(15 * sample_rate):
        t = n / sample_rate; beat = t % 0.5
        envelope = min(1, beat / 0.03) * max(0, 1-beat/0.5)
        val = 700*envelope*math.sin(2*math.pi*notes[int(t/0.5)%len(notes)]*t)
        for hit in (2,11):
            dt=t-hit
            if 0 <= dt < 0.14:
                val += 1100*(1-dt/0.14)*math.sin(2*math.pi*(700*dt-600*dt*dt))
        pcm.append(int(max(-32768,min(32767,val))))
    with wave.open(str(OUT/'music.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sample_rate); f.writeframes(pcm.tobytes())


def render():
    for i, dur in enumerate(DURATIONS):
        # Yavaş yakınlaşma: görsel motoru sabit 3D görselleri hareketlendirir.
        zoom=f"zoompan=z='min(zoom+0.00018,1.05)':d=1:s={W}x{H}:fps={FPS}"
        cmd('ffmpeg','-v','error','-y','-loop','1','-framerate',str(FPS),'-i',OUT/f'image{i}.png',
            '-i',OUT/f'voice{i}.wav','-vf',zoom+',format=yuv420p','-t',str(dur),
            '-c:v','libx264','-preset','veryfast','-crf','21','-c:a','aac','-b:a','128k',
            '-shortest',OUT/f'scene{i}.mp4')
    (OUT/'concat.txt').write_text(''.join(f"file 'scene{i}.mp4'\n" for i in range(3)), encoding='utf8')
    cmd('ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',OUT/'concat.txt','-c','copy',OUT/'joined.mp4')
    music()
    cmd('ffmpeg','-v','error','-y','-i',OUT/'joined.mp4','-i',OUT/'music.wav',
        '-filter_complex','[0:v]ass=output/captions.ass[v];[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]',
        '-map','[v]','-map','[a]','-t','15','-r','30','-c:v','libx264','-preset','veryfast','-crf','20',
        '-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',OUT/'shorts.mp4')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--fact', default=''); args = ap.parse_args()
    if not os.environ.get('GEMINI_API_KEY'): raise SystemExit('GEMINI_API_KEY eksik; GitHub Actions secret olarak ekleyin')
    OUT.mkdir(exist_ok=True)
    client, plan = plan_scenes(args.fact.strip())
    for i, scene in enumerate(plan['scenes']):
        print(f'Sahne {i+1}/3 görseli üretiliyor', flush=True); generate_image(client, scene, i)
    print('Türkçe ses ve altyazı hazırlanıyor', flush=True); make_audio_and_captions(plan)
    print('Video render ediliyor', flush=True); render()
    print('Hazır: output/shorts.mp4', flush=True)

if __name__ == '__main__': main()
