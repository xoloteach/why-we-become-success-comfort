import os,sys,json,math,time,subprocess,bisect,functools
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));os.chdir(ROOT);cv2.setNumThreads(1);FONTS=os.path.join(ROOT,'fonts')
W,H,FPS=1920,1080,30;PAPER=(238,244,247);INK=(15,21,22);RUST=(60,98,200);GOLD=(58,179,232);WHITE=(244,247,250)
scenes=json.load(open('v2/scene_plan.json'));starts=[s['start'] for s in scenes];meta=json.load(open('v2/upscale_report.json'));tl=json.load(open('timeline.json'));VO=tl['vo_end'];TOTAL=tl['total']
CH=['The life you imagine', 'The everyday detour', 'Comfortable moments accumulate', 'Busy is not progress', 'Now versus later', 'The present has an advantage', 'Practicing avoidance', 'Ambition meets environment', 'Easy pleasure, invisible progress', 'Make the right choice easier', 'Comfort as protection', 'The relief cycle', 'Start smaller', 'Evidence and self-trust', 'What you repeat becomes your life', 'Ordinary choices, different future', 'Choose what matters', 'Build your future today']
def ease(u):u=min(1,max(0,u));return 1-(1-u)**3
def spring(u):u=max(0,min(1,u));return (1-(1+7*u)*math.exp(-7*u))/(1-8*math.exp(-7))
@functools.lru_cache(maxsize=800)
def glyph(t,size=34,col=INK,width=800,weight='ExtraBold'):
 font=ImageFont.truetype(f'{FONTS}/Montserrat-{weight}.ttf',size);d=ImageDraw.Draw(Image.new('RGBA',(1,1)));ls=[]
 for part in t.split('\n'):
  cur=''
  for word in part.split():
   z=(cur+' '+word).strip()
   if d.textlength(z,font=font)>width and cur:ls.append(cur);cur=word
   else:cur=z
  if cur:ls.append(cur)
 if not ls:ls=[' ']
 ht=round(size*1.24);ww=min(width,math.ceil(max(d.textlength(z,font=font) for z in ls)))+8;im=Image.new('RGBA',(ww,len(ls)*ht+12));d=ImageDraw.Draw(im)
 for i,z in enumerate(ls):d.text((3,i*ht-size*.12),z,font=font,fill=col[::-1]+(255,))
 return np.ascontiguousarray(np.asarray(im)[:,:,[2,1,0,3]])
def blit(f,im,x,y,alpha=1):
 if alpha<=0:return
 x,y=int(x),int(y);h,w=im.shape[:2];xa,ya=max(0,x),max(0,y);xb,yb=min(W,x+w),min(H,y+h)
 if xb<=xa or yb<=ya:return
 src=im[ya-y:yb-y,xa-x:xb-x];a=src[:,:,3:4].astype(np.float32)*(alpha/255);dst=f[ya:yb,xa:xb];dst[:]=(dst*(1-a)+src[:,:,:3]*a).astype(np.uint8)
def text(f,t,x,y,size=34,col=INK,width=800,alpha=1,weight='ExtraBold',center=False):
 a=glyph(t,size,col,width,weight);blit(f,a,x-a.shape[1]/2 if center else x,y,alpha);return a.shape[0]
def line(f,a,b,col=RUST,th=4,p=1):
 if p<=0:return
 a=np.array(a,float);b=a+(np.array(b,float)-a)*min(1,p);cv2.line(f,tuple(a.astype(int)),tuple(b.astype(int)),col,th,cv2.LINE_AA)
def path(f,pts,col=RUST,th=5,p=1,arrow=False):
 if p<=0:return
 pts=np.array(pts,float);lens=np.linalg.norm(np.diff(pts,axis=0),axis=1);left=lens.sum()*min(1,p);out=[pts[0]]
 for i,L in enumerate(lens):
  if left>=L:out.append(pts[i+1]);left-=L
  else:out.append(pts[i]+(pts[i+1]-pts[i])*(left/max(L,.001)));break
 out=np.array(out,np.int32);cv2.polylines(f,[out],False,col,th,cv2.LINE_AA)
 if arrow and len(out)>1 and p>.94:
  v=out[-1]-out[-2];v=v/max(np.linalg.norm(v),.001);n=np.array([-v[1],v[0]]);tip=out[-1];cv2.fillConvexPoly(f,np.array([tip,tip-v*20+n*10,tip-v*20-n*10],np.int32),col,cv2.LINE_AA)
def rect(f,x,y,w,h,col):
 x,y,w,h=map(int,(x,y,w,h));r=13;cv2.rectangle(f,(x+r,y),(x+w-r,y+h),col,-1);cv2.rectangle(f,(x,y+r),(x+w,y+h-r),col,-1)
 for cx,cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:cv2.circle(f,(cx,cy),r,col,-1,cv2.LINE_AA)
rng=np.random.default_rng(12);grain=rng.normal(0,.55,(H,W,1));BG={False:np.clip(np.array(PAPER)[None,None,:]+grain,0,255).astype(np.uint8),True:np.clip(np.array(INK)[None,None,:]+grain*.45,0,255).astype(np.uint8)}
for dark in (False,True):cv2.line(BG[dark],(90,139),(1830,139),(40,47,52) if dark else (228,235,240),1,cv2.LINE_AA)
@functools.lru_cache(maxsize=6)
def hero(art,feature=False,dark=False):
 s,p=art.split('-');a=cv2.imread(f'v2/layers/s{s}_p{p}.png',-1);x0,y0,x1,y1=meta[art]['bbox'];x0=max(0,x0-8);y0=max(0,y0-8);x1=min(a.shape[1],x1+8);y1=min(a.shape[0],y1+8);a=a[y0:y1,x0:x1];h,w=a.shape[:2];scale=min((490 if feature else 850)/w,(400 if feature else 590)/h);a=cv2.resize(a,(round(w*scale),round(h*scale)),interpolation=cv2.INTER_AREA)
 al=a[:,:,3];ns,lab,stats,cent=cv2.connectedComponentsWithStats((al>80).astype(np.uint8),8)
 for j in range(1,ns):
  if stats[j,cv2.CC_STAT_AREA]<28:al[lab==j]=0
 if dark: # Intentional paper-cut backing avoids pale-interior / halo faults on obsidian.
  yy,xx=np.where(al>120)
  if len(xx):hull=cv2.convexHull(np.column_stack([xx,yy]).astype(np.int32));back=np.zeros_like(al);cv2.fillConvexPoly(back,hull,255);al=np.maximum(al,back)
 a[:,:,3]=cv2.GaussianBlur(al,(3,3),.35);gray=cv2.cvtColor(a[:,:,:3],cv2.COLOR_BGR2GRAY);ink=a.copy();ink[:,:,:3]=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR);ink[:,:,3]=(a[:,:,3]*np.clip((220-gray)/80,0,1)).astype(np.uint8)
 den=(a[:,:,3]/255).mean(0);aw=a.shape[1];lo,hi=int(aw*.28),int(aw*.72);cut=lo+int(np.argmin(den[lo:hi])) if hi>lo else aw//2;parts=[(a,0)]
 if den[cut]<.015 and cut>aw*.2 and cut<aw*.8:parts=[(a[:,:cut].copy(),0),(a[:,cut:].copy(),cut)]
 return a,ink,parts
def art_draw(f,s,t):
 feat=s['feature'];a,ink,parts=hero(s['art'],feat,s['dark']);ah,aw=a.shape[:2];r=t-s['start'];D=s['end']-s['start'];u=max(0,min(1,r/D));cx=340 if feat else (1405 if s['layout']=='right' else 515);cy=665 if feat else 548;x=cx-aw/2;y=cy-ah/2;ent=spring(r/.85);px=(1-ent)*46*(1 if s['layout']=='right' else -1);drift=(ease(u)-.5)*15*(1 if s['id']%2==0 else -1);reveal=ease(r/.72);fill=ease((r-.18)/.82)
 for j,(im,off) in enumerate(parts):
  dy=(1-spring(max(0,r-j*.1)/.85))*(26 if j==0 else -28)+(ease(u)-.5)*(4 if j==0 else -6);dx=px+drift*(.8 if j==0 else 1.0)
  cap=min(im.shape[1],int(aw*reveal)-off)
  if cap>0:blit(f,ink[:,off:off+cap],x+off+dx,y+dy,1-fill);blit(f,im[:,:cap],x+off+dx,y+dy,fill)
def diagram(f,s,t,x,y,w=790,h=320):
 kind=s['kind'];r=t-s['start'];D=s['end']-s['start'];labels=s['labels'];n=len(labels);dark=s['dark'];fg=WHITE if dark else INK;muted=(155,164,174) if dark else (114,121,127);soft=(33,42,48) if dark else (221,231,239);cue=s['cues'];rev=[spring((t-c)/.55) for c in cue];pr=ease((r-.16)/.8);cur=max([i for i,c in enumerate(cue) if t>=c] or [-1])
 if kind in ('feed','stack'):
  rh=min(62,(h-8-(n-1)*12)/n)
  for i,l in enumerate(labels):
   a=rev[i]
   if a<=0:continue
   yy=y+i*(rh+12);xx=x+(1-a)*60;active=i==cur;col=RUST if active else soft;tc=WHITE if active else fg;rect(f,xx,yy,w-8,rh,col);text(f,f'{i+1:02d}',xx+18,yy+12,23,tc,65,alpha=a);text(f,l,xx+88,yy+9,28,tc,w-110,alpha=a);line(f,(xx+18,yy+rh-3),(xx+w-24,yy+rh-3),GOLD,3,ease((t-cue[i])/.7))
 elif kind in ('thought','focus'):
  if kind=='focus':cv2.ellipse(f,(x+48,y+60),(36,36),-90,0,360*pr,RUST,4,cv2.LINE_AA)
  gap=min(104,h/max(n,1));off=108 if kind=='focus' else 25
  for i,l in enumerate(labels):
   yy=y+i*gap;a=rev[i];line(f,(x,yy+8),(x,yy+57),RUST if i==cur else muted,5,a);text(f,l,x+off+(1-a)*25,yy+7,36 if n<=2 else 31,RUST if i==cur else fg,w-off-10,alpha=a)
 elif kind in ('split','balance','meter','window'):
  if kind=='window':
   yy=y+24;line(f,(x+165,yy+84),(x+w-180,yy+84),muted,2,pr)
   for i in range(min(n,2)):
    sz=105 if i==0 else 205;xx=x+25 if i==0 else x+w-245;a=rev[i]
    if a>0:
     cv2.rectangle(f,(int(xx),int(yy)),(int(xx+sz*a),int(yy+sz)),RUST if i==0 else fg,3,cv2.LINE_AA)
     for j in range(1 if i==0 else 4):line(f,(xx+15,yy+25+j*35),(xx+sz-15,yy+25+j*35),muted,2,a)
     text(f,labels[i],xx-10,yy+sz+18,27,fg,290,alpha=a)
  elif kind=='meter':
   for i,l in enumerate(labels[:2]):
    yy=y+20+i*146;a=rev[i];text(f,l,x,yy,30,fg,w,alpha=a);line(f,(x,yy+69),(x+w-35,yy+69),soft,14,pr);L=w-35
    if s['art']=='01-3' and i==1:L*=1-.57*ease((t-5.4)/2)
    elif i==1:L*=.62
    line(f,(x,yy+69),(x+L,yy+69),RUST if i else fg,14,a)
    if a>0:cv2.circle(f,(int(x+L*a),int(yy+69)),10,RUST if i else fg,-1,cv2.LINE_AA)
  else:
   line(f,(x+w/2,y),(x+w/2,y+h-10),muted,2,pr)
   for i in range(min(n,2)):
    a=rev[i];cx=x+w*(.25 if i==0 else .75);cy=y+155;text(f,labels[i],cx,y+12,29,fg,int(w/2-38),alpha=a,center=True)
    if a>0:
     cv2.ellipse(f,(int(cx),int(cy)),(55,55),-90,0,360*a,RUST if i else fg,4,cv2.LINE_AA);text(f,'PART' if kind=='balance' and i==0 else ('WHOLE' if kind=='balance' else ('A' if i==0 else 'B')),cx,cy-19,25 if kind=='balance' else 37,fg,140,alpha=a,center=True)
    line(f,(cx-92,y+245),(cx+92,y+245),RUST if i else muted,4,a)
   if n>2:text(f,labels[-1],x+20,y+276,26,RUST,w-40,alpha=rev[-1])
 elif kind=='dots':
  for i in range(100):
   xx=x+20+i%10*27;yy=y+4+i//10*27;a=ease((r-i*.003)/.6);hot=i>=95 and (t>=168.2 or s['start']>=170);col=RUST if hot else (muted if t>=164.4 else fg);cv2.circle(f,(int(xx),int(yy)),max(1,int(7*a)),col,-1,cv2.LINE_AA)
  bx=x+350;hot=t>=168.2 or s['start']>170;text(f,'5' if hot else ('95' if t>=164.4 else '100'),bx,y+10,136,RUST if hot else fg,460,alpha=pr,weight='Black');text(f,'EXCITING' if hot else ('ORDINARY' if t>=164.4 else 'PEOPLE'),bx,y+175,37,fg,460,alpha=pr);text(f,'THOUGHT EXPERIMENT',bx,y+254,23,muted,460)
 elif kind in ('paths','timeline','finish','stairs'):
  if kind=='stairs':
   pts=[(x+24,y+212),(x+150,y+212),(x+150,y+159),(x+300,y+159),(x+300,y+106),(x+450,y+106),(x+450,y+53),(x+w-35,y+53)];path(f,pts,RUST,5,ease(r/1.8),True)
   for i in range(4):cv2.circle(f,(int(x+85+i*162),int(y+212-i*53)),max(1,int(10*ease((r-.2-i*.35)/.55))),fg,-1,cv2.LINE_AA)
   if n<=2:
    for i,l in enumerate(labels):text(f,l,x+18,y+252+i*36,27,fg,w-35,alpha=rev[i])
   elif cur>=0:text(f,labels[cur],x+18,y+275,31,RUST,w-35,alpha=rev[cur])
  elif kind=='finish':
   xx=int(x+300+ease((t-265.9)/1.2)*280);line(f,(x,y+225),(x+w-25,y+225),muted,3,pr);line(f,(xx,y+30),(xx,y+226),RUST,5,pr)
   for i in range(2):
    for j in range(4):cv2.rectangle(f,(xx+j*21,y+30+i*21),(xx+(j+1)*21,y+30+(i+1)*21),fg if (i+j)%2 else RUST,-1)
   path(f,[(x+35,y+153),(x+220,y+153)],RUST,6,ease(r/.8),True)
   for i,l in enumerate(labels):text(f,l,x+15+i*245,y+269,25,fg,230,alpha=rev[i])
  else:
   for i in range(min(n,2)):
    yy=y+85+i*144;a=rev[i];text(f,labels[i],x,yy-51,28,fg,w,alpha=a);pts=[(x+15,yy),(x+w-20,yy)] if kind=='timeline' or i==0 else [(x+15,yy),(x+150,yy),(x+300,yy-30),(x+440,yy+20),(x+610,yy),(x+w-20,yy-45)];path(f,pts,muted if i==0 else RUST,4,a,True);u=min(.86,r/max(D,1)*.65+.12);points=np.array(pts,float);lengths=np.linalg.norm(np.diff(points,axis=0),axis=1);distance=lengths.sum()*u;seg=0
    while seg<len(lengths)-1 and distance>lengths[seg]:distance-=lengths[seg];seg+=1
    q=points[seg]+(points[seg+1]-points[seg])*distance/max(lengths[seg],.001);px,py=q
    if a>.8:cv2.circle(f,(int(px),int(py)),11,RUST if i else fg,-1,cv2.LINE_AA)
   if n>2 and cur>=2:text(f,labels[cur],x+10,y+h-24,28,RUST,w-20,alpha=rev[cur])
 elif kind=='loop':
  lw=(w-120)/2;lh=105;pos=[(x,y),(x+w-lw,y),(x+w-lw,y+204),(x,y+204)]
  for i,(xx,yy) in enumerate(pos):
   a=rev[min(i,n-1)]
   if a>0:rect(f,xx+(1-a)*14,yy,lw,lh,RUST if i==cur else soft);text(f,labels[min(i,n-1)],xx+lw/2,yy+24,28,WHITE if i==cur else fg,int(lw-38),alpha=a,center=True)
  links=[[(x+lw,y+53),(x+w-lw-13,y+53)],[(x+w-lw/2,y+107),(x+w-lw/2,y+191)],[(x+w-lw,y+256),(x+lw+13,y+256)],[(x+lw/2,y+204),(x+lw/2,y+119)]]
  for i,p in enumerate(links):
   if rev[i]>.2 and rev[(i+1)%4]>.2:path(f,p,RUST,5,ease((t-cue[min(i,n-1)]-.25)/.65),True)
  if all(a>.9 for a in rev):
   u=((r-1.5)*.16)%4;j=int(u);a,b=map(np.array,(links[j][0],links[j][-1]));q=a+(b-a)*(u-j);cv2.circle(f,tuple(q.astype(int)),6,GOLD,-1,cv2.LINE_AA)
 elif kind=='network':
  cx=x+w/2;cy=y+145
  for i in range(14):
   ang=i*2*math.pi/14;rad=110 if i%2 else 155;xx=cx+rad*1.85*math.cos(ang);yy=cy+rad*.7*math.sin(ang);a=ease((r-i*.03)/.75);line(f,(cx,cy),(xx,yy),muted,1,a)
   if a>.5:cv2.circle(f,(int(xx),int(yy)),int(12*a),RUST if i%5==0 else fg,-1,cv2.LINE_AA)
  cv2.circle(f,(int(cx),int(cy)),24,RUST,-1,cv2.LINE_AA)
  if cur>=0:text(f,labels[cur],cx,y+290,28,fg,w-30,alpha=rev[cur],center=True)
 elif kind=='search':
  rect(f,x,y+20,w-15,85,soft);text(f,labels[0][:int(len(labels[0])*ease((t-cue[0])/1.1))],x+26,y+41,31,fg,w-130);cv2.circle(f,(x+w-65,y+57),17,RUST,3,cv2.LINE_AA);line(f,(x+w-53,y+70),(x+w-36,y+87),RUST,4)
  for i in range(3):
   a=ease((r-.9-i*.26)/.5);yy=y+145+i*60;line(f,(x+18,yy),(x+625-i*80,yy),muted,8,a)
   if a>.8:cv2.circle(f,(x+w-49,yy),8,RUST,-1,cv2.LINE_AA)
  if n>1:text(f,labels[1],x+18,y+316,26,RUST,w,alpha=rev[1])
 elif kind=='counter':
  if s['art']=='03-6':text(f,'MILLIONS',x,y+24,92,RUST,w,alpha=rev[0],weight='Black');text(f,'OF POSSIBLE COMPARISONS',x,y+145,26,fg,w,alpha=rev[0]);text(f,labels[1],x,y+235,35,fg,w,alpha=rev[1])
  elif s['art']=='06-8':text(f,str(round(50*ease((t-cue[0])/1.2))),x,y+6,140,RUST,w,alpha=pr,weight='Black');text(f,'BOOKS / YEAR',x+230,y+80,34,fg,650);text(f,labels[1],x,y+230,34,fg,w,alpha=rev[1])
  else:
   text(f,'0',x,y+8,154,RUST,w,alpha=pr,weight='Black')
   for i,l in enumerate(labels):text(f,l,x+230,y+36+i*72,31,fg,w-240,alpha=rev[i])
 elif kind=='clock':
  cx=x+120;cy=y+145;a=rev[0];cv2.ellipse(f,(cx,cy),(103,103),-90,0,360*a,RUST,4,cv2.LINE_AA)
  if a>0:
   ang=-math.pi/2+ease((t-cue[0])/1.4)*math.pi/3;line(f,(cx,cy),(cx+67*math.cos(ang),cy+67*math.sin(ang)),fg,5,a);line(f,(cx,cy),(cx,cy-84),fg,3,a)
  text(f,'10 MIN',x+278,y+49,74,RUST,w-278,alpha=a,weight='Black')
  if n>1:text(f,labels[1],x+278,y+166,28,fg,w-278,alpha=rev[1])
 elif kind=='switch':
  xx=x+20;yy=y+30;u=ease((t-cue[1])/.7) if len(cue)>1 else 0;rect(f,xx,yy,300,90,RUST if u<.5 else soft);cv2.circle(f,(int(xx+250-200*u),yy+45),32,fg,-1,cv2.LINE_AA)
  for i,l in enumerate(labels):text(f,l,x+380,y+42+i*104,39,fg,w-380,alpha=rev[i])
  line(f,(x+20,y+245),(x+w-20,y+245),RUST,4,ease((r-.5)/.8))
 elif kind=='iceberg':
  yy=y+112;line(f,(x,yy),(x+w-30,yy),muted,2,pr);text(f,labels[0],x+20,y+25,31,fg,w-40,alpha=rev[0]);text(f,labels[1],x+20,y+287,30,RUST,w-40,alpha=rev[1])
  for i in range(4):path(f,[(x+w/2,yy),(x+w/2+(i-1.5)*80,yy+68),(x+w/2+(i-1.5)*140,yy+165)],RUST,2,ease((r-.2*i)/1.1))
def scene_frame(i,t):
 s=scenes[i];r=t-s['start'];f=BG[s['dark']].copy();fg=WHITE if s['dark'] else INK;feat=s['feature'];tx=100 if feat or s['layout']=='right' else 1035;maxw=1720 if feat else 785;text(f,'WHY WE BECOME',90,62,26,fg,470,weight='Black');text(f,f'{s["chapter"]:02d} / {CH[s["chapter"]-1].upper()}',790,65,24,RUST,1000);title=s['title'].replace('\n',' ') if feat else s['title'];sz=86 if feat else 78;im=glyph(title,sz,fg,maxw,'Black')
 while im.shape[0]>225 and sz>54:sz-=2;im=glyph(title,sz,fg,maxw,'Black')
 a=spring(r/.55);blit(f,im,tx,214+(1-a)*22,a);line(f,(tx,440),(tx+150,440),RUST,5,ease((r-.18)/.7));art_draw(f,s,t);diagram(f,s,t,660 if feat else tx,502,1150 if feat else 775,320);line(f,(90,1025),(1830,1025),(54,61,66) if s['dark'] else (216,225,232),2);line(f,(90,1025),(1830,1025),RUST,3,t/TOTAL);return f
end=cv2.resize(cv2.imread('assets/subscribe-end-card.jpeg'),(W,H),interpolation=cv2.INTER_LANCZOS4)
def frame(t):
 if t>=VO:
  a=ease((t-VO)/.65);f=cv2.addWeighted(scene_frame(len(scenes)-1,VO-.01),1-a,end,a,0);return f
 i=max(0,bisect.bisect_right(starts,t)-1);f=scene_frame(i,t);r=t-scenes[i]['start']
 if i and r<.24:
  prev=scene_frame(i-1,scenes[i]['start']-.02);a=ease(r/.24)
  if i%4==0 and scenes[i]['dark']==scenes[i-1]['dark']:b=int(W*a);f[:,b:]=prev[:,b:];cv2.line(f,(b,0),(b,H),RUST,3)
  else:f=cv2.addWeighted(prev,1-a,f,a,0)
 return f
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='stills':
  for i,s in enumerate(scenes):cv2.imwrite(f'v2/qa/scene{i:03d}.png',frame(min(s['end']-.06,s['start']+max(.7,(s['end']-s['start'])*.66))))
  print('stills',len(scenes));sys.exit(0)
 start=float(sys.argv[1]) if len(sys.argv)>1 else 0;stop=float(sys.argv[2]) if len(sys.argv)>2 else TOTAL;out=sys.argv[3] if len(sys.argv)>3 else 'final-v2-motion.mp4';vf=f'setpts=PTS+{start}/TB,ass=v2/captions.ass:fontsdir={FONTS},setpts=PTS-STARTPTS';cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s','1920x1080','-r','30','-i','-','-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-an','-movflags','+faststart',out];p=subprocess.Popen(cmd,stdin=subprocess.PIPE);n0,n1=round(start*FPS),round(min(stop,TOTAL)*FPS);t0=time.time()
 try:
  for n in range(n0,n1):
   p.stdin.write(frame(n/FPS).tobytes())
   if (n-n0)%300==0:print(f'{n-n0}/{n1-n0} {time.time()-t0:.1f}s',flush=True)
 finally:p.stdin.close()
 rc=p.wait();print('DONE',out,rc,time.time()-t0,flush=True);sys.exit(rc)
