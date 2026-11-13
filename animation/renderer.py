"""Pillow ile kare kare 2D çizim. Kod çalıştıran dinamik sahne komutu yoktur."""
import math
from PIL import Image, ImageDraw, ImageFont
from .schema import validate

COLORS = {
    'ocean': ((10,34,74),(14,105,135),(91,221,228)),
    'sunset': ((71,27,70),(201,82,72),(255,198,103)),
    'forest': ((15,51,53),(47,126,93),(188,239,153)),
    'violet': ((33,25,79),(92,63,154),(243,171,227)),
}

def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)

def ease_out_back(t):
    t=max(0,min(1,t))-1
    return 1+2.7*t**3+1.7*t**2

def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','DejaVuSans-Bold.ttf'):
        try: return ImageFont.truetype(p,size)
        except OSError: pass
    return ImageFont.load_default()

def gradient(w,h,top,bottom):
    im=Image.new('RGB',(1,h)); pix=im.load()
    for y in range(h):
        k=y/max(1,h-1); pix[0,y]=tuple(round(top[i]*(1-k)+bottom[i]*k) for i in range(3))
    return im.resize((w,h))

def background(d, bg, palette, t, w, h):
    accent=palette[2]; s=w/540
    # İki parçacık katmanı farklı hızlarda kayar: düşük maliyetli parallax.
    for layer in range(2):
        for i in range(18):
            x=(i*197+43*layer+math.sin(t*(0.3+layer*.15)+i)*35*layer)%540*s
            y=((i*239+78*layer-t*(7+8*layer))%960)*h/960
            r=(2+layer*2)*s
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,65+layer*35))
    if bg=='ocean':
        for i in range(5):
            x=(40+i*110+math.sin(t*0.5+i)*20)*s
            d.polygon([(x,0),(x+80*s,0),(x+190*s,h),(x+100*s,h)],fill=(120,236,255,15))
    elif bg=='space':
        for i in range(15):
            x=(i*103%520+10)*s; y=(i*193%600+35)*h/960
            d.line((x-4*s,y,x+4*s,y),fill=(255,255,255,180),width=max(1,round(s)))
            d.line((x,y-4*s,x,y+4*s),fill=(255,255,255,180),width=max(1,round(s)))
    elif bg=='nature':
        for i in range(8):
            x=(i*80-40)*s; d.ellipse((x,h*.78,x+140*s,h*1.05),fill=(18,90,62,100))
    elif bg=='lab':
        for i in range(7):
            y=h*(.14+i*.11); d.line((0,y,w,y),fill=(180,255,250,22),width=max(1,round(s)))
            x=w*(.1+i*.14); d.line((x,0,x,h),fill=(180,255,250,22),width=max(1,round(s)))

def heart(d,x,y,r,color):
    d.ellipse((x-r,y-r,x,y),fill=color); d.ellipse((x,y-r,x+r,y),fill=color)
    d.polygon(((x-r,y-r/2),(x+r,y-r/2),(x,y+r)),fill=color)

def character(d,name,cx,cy,r,t,animation,accent):
    bob=math.sin(t*2.4)*r*.05; cy+=bob
    if animation=='enter_bounce': r*=max(.05,ease_out_back(t/.6))
    elif animation=='pulse': r*=1+.08*math.sin(t*5)
    outline=(13,25,53,255); col=(255,128,124,255)
    if name=='octopus':
        for j in range(8):
            ang=math.pi*(.15+j*.1); dx=math.cos(ang); dy=math.sin(ang)
            x1=cx+dx*r*.55; y1=cy+r*.3
            x2=cx+dx*r*(1.1+0.08*math.sin(t*4+j)); y2=cy+dy*r*(.85+0.08*math.cos(t*4+j))
            d.line((x1,y1,x2,y2),fill=outline,width=max(4,round(r*.24)))
            d.line((x1,y1,x2,y2),fill=col,width=max(3,round(r*.18)))
            d.ellipse((x2-r*.10,y2-r*.10,x2+r*.10,y2+r*.10),fill=col)
        d.ellipse((cx-r*.75,cy-r*.92,cx+r*.75,cy+r*.54),fill=col,outline=outline,width=max(2,round(r*.035)))
        blink = (t%4.3)<.13
        for sx in (-.27,.27):
            xx=cx+sx*r; yy=cy-r*.18
            d.ellipse((xx-r*.15,yy-r*.16*(.1 if blink else 1),xx+r*.15,yy+r*.16*(.1 if blink else 1)),fill='white')
            if not blink: d.ellipse((xx-r*.065,yy-r*.07,xx+r*.065,yy+r*.07),fill=outline)
        d.arc((cx-r*.16,cy+r*.04,cx+r*.16,cy+r*.25),0,180,fill=outline,width=max(2,round(r*.025)))
    elif name=='heart': heart(d,cx,cy,r*.75,(255,103,133,255))
    elif name=='planet':
        d.ellipse((cx-r*.85,cy-r*.85,cx+r*.85,cy+r*.85),fill=(112,176,252,255),outline=outline,width=max(2,round(r*.04)))
        d.ellipse((cx-r*1.2,cy-r*.25,cx+r*1.2,cy+r*.3),outline=(255,218,145,255),width=max(3,round(r*.08)))
    elif name=='star':
        pts=[]
        for j in range(10):
            a=-math.pi/2+j*math.pi/5; rr=r if j%2==0 else r*.44; pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
        d.polygon(pts,fill=(255,213,91,255),outline=outline,width=max(2,round(r*.03)))
    elif name=='atom':
        for ang in (0,60,120):
            # Farklı açılı yörüngeyi hesaplanmış nokta dizileriyle çiz.
            pts=[]; a=math.radians(ang)
            for n in range(61):
                q=n*math.tau/60; x=r*math.cos(q); y=r*.3*math.sin(q)
                pts.append((cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a)))
            d.line(pts,fill=(*accent,255),width=max(3,round(r*.04)))
        d.ellipse((cx-r*.18,cy-r*.18,cx+r*.18,cy+r*.18),fill=(255,205,91,255))
    elif name=='book':
        d.rounded_rectangle((cx-r*.8,cy-r*.8,cx+r*.8,cy+r*.8),radius=round(r*.1),fill=(244,227,195,255),outline=outline,width=max(2,round(r*.04)))
        d.line((cx,cy-r*.75,cx,cy+r*.75),fill=outline,width=max(2,round(r*.035)))
        for side in (-1,1):
            for j in range(3):
                x=cx+side*r*.4; y=cy-r*.4+j*r*.3; d.line((x-r*.2,y,x+r*.2,y),fill=(110,122,136,255),width=max(2,round(r*.025)))
    elif name=='bulb':
        d.ellipse((cx-r*.65,cy-r*.9,cx+r*.65,cy+r*.4),fill=(255,219,95,255),outline=outline,width=max(2,round(r*.04)))
        d.rounded_rectangle((cx-r*.3,cy+r*.25,cx+r*.3,cy+r*.7),radius=round(r*.08),fill=(200,210,220,255),outline=outline,width=max(2,round(r*.04)))
    if animation == 'orbit':
        for j in range(3):
            a=t*1.5+j*math.tau/3
            x=cx+math.cos(a)*r*1.25; y=cy+math.sin(a)*r*.6
            d.ellipse((x-r*.08,y-r*.08,x+r*.08,y+r*.08),fill=(*accent,255))
    if animation in ('pulse','blood_flow'):
        for j in range(3):
            x=cx+(j-1)*r*.65; y=cy-r*1.42-abs(math.sin(t*3+j))*.08*r
            heart(d,x,y,r*.18,(255,111+j*25,150,255))
    if animation=='blood_flow':
        for j in (-1,1):
            x0=cx+j*r*.42; x1=cx+j*r*1.15; yy=cy+r*.82
            d.line((x0,yy,x1,yy),fill=(255,230,156,255),width=max(2,round(r*.04)))
            d.polygon(((x1,yy),(x1-j*r*.16,yy-r*.10),(x1-j*r*.16,yy+r*.10)),fill=(255,230,156,255))

def draw_text(d,text,w,h,t,accent):
    s=w/540; f=font(max(12,round(46*s))); words=text.split(); lines=[]; cur=''
    for wd in words:
        candidate=(cur+' '+wd).strip()
        if cur and d.textlength(candidate,font=f)>w*.85: lines.append(cur); cur=wd
        else: cur=candidate
    if cur: lines.append(cur)
    lines=lines[:3]; y=h*.13
    for line in lines:
        bb=d.textbbox((0,0),line,font=f,stroke_width=max(1,round(2*s))); x=(w-(bb[2]-bb[0]))/2
        d.text((x,y),line,font=f,fill=(255,255,255,255),stroke_width=max(1,round(3*s)),stroke_fill=(18,25,48,255)); y+=56*s
    d.rounded_rectangle((w*.36,y+12*s,w*.64,y+18*s),radius=3*s,fill=(*accent,255))

def frame(plan, t, width=1080, height=1920, validated=False):
    if not validated: validate(plan)
    idx=0 if t<3 else 1 if t<10 else 2
    scene=plan['scenes'][idx]; local=t-scene['start']; palette=COLORS[scene['palette']]
    base=gradient(width,height,palette[0],palette[1]).convert('RGBA')
    layer=Image.new('RGBA',(width,height)); d=ImageDraw.Draw(layer)
    background(d,scene['background'],palette,local,width,height)
    # Kara kutu okunurluk için; bu alan altyazıdan yukarıda kalır.
    d.rounded_rectangle((width*.06,height*.08,width*.94,height*.31),radius=int(width*.05),fill=(5,15,35,55))
    draw_text(d,scene['text'],width,height,local,palette[2])
    character(d,scene['character'],width/2,height*.55,width*.27,local,scene['animation'],palette[2])
    base=Image.alpha_composite(base,layer)
    # Sahne geçişinde siyaha kısa fade.
    dist=min(local,scene['end']-t); opacity=round(255*(1-smooth(dist/.18))) if dist<.18 else 0
    if opacity>0: base=Image.alpha_composite(base,Image.new('RGBA',base.size,(0,0,0,opacity)))
    return base.convert('RGB')
