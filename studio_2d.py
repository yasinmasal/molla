"""Gemini + Edge TTS + Pillow 2D + FFmpeg; görsel/video modeli kullanmaz."""
import argparse, asyncio, json, os
from pathlib import Path
from google.genai import types
import studio
from animation.schema import validate, BACKGROUNDS, CHARACTERS, ANIMATIONS, PALETTES
from animation.preview import render

OUT=studio.OUT
DURATIONS=[3.0,7.0,5.0]


def storyboard(client, old):
    prompt=("Aşağıdaki araştırılmış Türkçe video planını güvenli 2D animasyon planına dönüştür. "
      "Yeni olgu ekleme. Yalnız JSON döndür: title, description, duration=15, scenes dizisi. "
      "Tam üç sahne olsun: id/start/end sırasıyla 1/0/3, 2/3/10, 3/10/15. "
      "Her sahneye background, character, animation, palette, text ve narration ekle. "
      "İlk sahne en çok 5, ikinci en çok 12, üçüncü en çok 8 Türkçe kelime; doğal sesli okunuşu kısa olsun. "
      "Text 60 karakterden kısa. Bileşenler sadece bu listelerden: "
      f"background={BACKGROUNDS}; character={CHARACTERS}; animation={ANIMATIONS}; palette={PALETTES}. "
      "Konu nesne kütüphanesinde yoksa en uygun soyut/book/bulb/atom öğesini kullan, var olmayan komut uydurma. "
      "Plan: "+json.dumps(old,ensure_ascii=False))
    model=os.environ.get('TEXT_MODEL','gemini-2.5-flash')
    last=''
    for attempt in range(3):
        r=client.models.generate_content(model=model, contents=prompt+'\nÖnceki hata: '+last,
            config=types.GenerateContentConfig(response_mime_type='application/json'))
        try: return validate(json.loads(r.text))
        except (ValueError,TypeError,KeyError) as e: last=str(e)
    raise ValueError('Storyboard üç denemede doğrulanamadı: '+last)


def write_subtitles(entries):
    (OUT/'captions.srt').write_text('\n\n'.join(f'{i}\n{studio.srt_time(a)} --> {studio.srt_time(b)}\n{w}' for i,(a,b,w) in enumerate(entries,1))+'\n',encoding='utf8')
    header='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,82,&H00FFFFFF,&H000000FF,&H00100804,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,80,80,250,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
    lines=[f'Dialogue: 0,{studio.ass_time(a)},{studio.ass_time(b)},Default,,0,0,0,,{studio.ass_escape(w)}' for a,b,w in entries]
    (OUT/'captions.ass').write_text(header+'\n'.join(lines)+'\n',encoding='utf8')


def make_audio(client, plan):
    """Süreye uymayan cümleyi kısaltıp yeniden seslendirir; hızlandırmaz."""
    entries=[]; model=os.environ.get('TEXT_MODEL','gemini-2.5-flash')
    for i,scene in enumerate(plan['scenes']):
        for attempt in range(3):
            mp3=OUT/f'voice{i}.mp3'
            words=asyncio.run(studio.tts(scene['narration'],mp3))
            if studio.media_duration(mp3)<=DURATIONS[i]-.1: break
            if attempt==2: raise ValueError(f'{i+1}. sahnedeki konuşma doğal hızla süreye sığmıyor')
            r=client.models.generate_content(model=model, contents=(
                'Bilimsel iddia eklemeden anlamı koruyarak bu Türkçe cümleyi çok daha kısa yaz. '
                'Yalnızca kısa cümleyi döndür: '+scene['narration']))
            shortened=(r.text or '').strip().strip('"“”')
            if not shortened: raise ValueError('Gemini kısa metin üretmedi')
            scene['narration']=shortened
        studio.cmd('ffmpeg','-v','error','-y','-i',mp3,'-af','apad','-t',DURATIONS[i],'-ar','44100','-ac','1',OUT/f'voice{i}.wav')
        for start,duration,word in words:
            a=scene['start']+start; b=min(scene['end']-.02,a+duration)
            if b>a: entries.append((a,b,word))
    write_subtitles(entries)


def assemble(plan):
    render(plan,OUT/'2d_silent.mp4')
    studio.music()
    studio.cmd('ffmpeg','-y','-v','error','-i',OUT/'2d_silent.mp4',
        '-i',OUT/'voice0.wav','-i',OUT/'voice1.wav','-i',OUT/'voice2.wav','-i',OUT/'music.wav',
        '-filter_complex',"[1:a][2:a][3:a]concat=n=3:v=0:a=1[narr];[narr][4:a]amix=inputs=2:duration=first:normalize=0[a];[0:v]ass=output/captions.ass[v]",
        '-map','[v]','-map','[a]','-t','15','-r','30','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',OUT/'shorts.mp4')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--fact',default=''); args=ap.parse_args()
    if not os.environ.get('GEMINI_API_KEY'): raise SystemExit('GEMINI_API_KEY eksik')
    OUT.mkdir(exist_ok=True)
    client, old=studio.plan_scenes(args.fact.strip())
    plan=storyboard(client,old)
    print('Türkçe ses hazırlanıyor; taşan cümleler kısaltılacak',flush=True)
    make_audio(client,plan)
    (OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
    print('2D kareler tek işlemle çiziliyor',flush=True)
    assemble(plan)
    print('Hazır: output/shorts.mp4',flush=True)

if __name__=='__main__': main()
