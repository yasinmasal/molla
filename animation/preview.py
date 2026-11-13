"""Önizleme/ham kare akışı: tek işlemci, kare dosyası biriktirmez."""
import argparse, json, subprocess
from pathlib import Path
from .renderer import frame
from .schema import validate

def render(plan, output, width=1080, height=1920, fps=30):
    validate(plan)
    if width%2 or height%2 or width<64 or height<64 or not 1<=fps<=60: raise ValueError('Geçersiz çözünürlük/FPS')
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(fps*15):
            process.stdin.write(frame(plan,i/fps,width,height,validated=True).tobytes())
        process.stdin.close()
    except BaseException:
        process.stdin.close(); process.terminate(); process.wait(); raise
    if process.wait()!=0: raise RuntimeError('FFmpeg render başarısız')
    return output

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',required=True); ap.add_argument('--output',default='output/2d-preview.mp4'); ap.add_argument('--width',type=int,default=1080); ap.add_argument('--height',type=int,default=1920); ap.add_argument('--fps',type=int,default=30)
    a=ap.parse_args(); plan=json.loads(Path(a.plan).read_text(encoding='utf8'))
    print('Render:',render(plan,a.output,a.width,a.height,a.fps))
if __name__=='__main__': main()
