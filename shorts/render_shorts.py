import os,sys,json,math,subprocess,wave,bisect,re,functools
from pathlib import Path
import cv2,numpy as np
R=Path(__file__).resolve().parents[1];os.chdir(R);sys.path.insert(0,str(R/'v2'))
import render_motion as B
B.W=1080;B.H=1920;W,H=1080,1920;cv2.setNumThreads(1)
O=R/'shorts/output';O.mkdir(parents=True,exist_ok=True);(O/'qa').mkdir(exist_ok=True)
WORDS=json.load(open('shorts/words-source.json'));P,I,RC,G,WH=B.PAPER,B.INK,B.RUST,B.GOLD,B.WHITE
CLIPS=[{'slug': '01-busy-is-not-progress', 'title': 'Comfort Can Look Productive', 'topic': 'BUSY ≠ PROGRESS', 'ranges': [[125.34, 130.135], [103.05, 123.255], [130.315, 140.47001]], 'duration': 37.65500999999999}, {'slug': '02-the-comfort-loop', 'title': 'You Are Practicing the Comfort Loop', 'topic': 'THE COMFORT LOOP', 'ranges': [[196.48499, 203.35998999999998], [369.24499999999995, 397.28002000000004]], 'duration': 37.41002000000006}, {'slug': '03-start-smaller', 'title': 'You Do Not Need a Perfect Routine', 'topic': 'START SMALLER', 'ranges': [[400.47999999999996, 435.565]], 'duration': 37.585000000000036}]
PLANS=['125.34;04-8;search;COMFORT CAN / LOOK PRODUCTIVE.;BUSY IS NOT PROGRESS;125.375\n103.085;04-4;split;BEGINNING / FEELS HARD.;THE TASK|THE EASY DETOUR;103.085,106.32\n108.0;04-5;stack;EASIER IS / NOT PROGRESS.;PHONE|COFFEE|FILES;108.0,109.2,110.4\n111.92;04-8;stack;EVERYTHING / EXCEPT THE TASK.;MESSAGES|ANOTHER VIDEO;111.92,113.2\n114.32;04-9;search;IT FELT / PRODUCTIVE.;YOU FELT BUSY;117.44\n119.534996;04-4;search;THE WORK / IS STILL WAITING.;THE IMPORTANT THING;120.735;dark\n130.35;04-9;split;TWO DIFFERENT / QUESTIONS.;BETTER IN SIX MONTHS?|BETTER RIGHT NOW?;131.79001,136.91\n134.59001;04-5;split;BETTER NOW? / OR BETTER LATER?;LONG-TERM LIFE|THIS MOMENT;131.79001,136.91\n138.51001;04-4;split;BUSY IS NOT / PROGRESS.;A BETTER LIFE|AN EASIER MOMENT;131.79001,136.91;dark', '196.48499;07-2;paths;COMFORT / TRAINS YOU.;THE CHOICE|THE NEXT CHOICE;196.51999,198.51999\n201.07999;07-3;paths;EVERY CHOICE / TEACHES.;YOUR ACTION|YOUR LEARNED RESPONSE;201.07999,201.07999\n369.28;12-1;loop;THE RELIEF / TRAP.;AVOID|RELIEF|GUILT|PROMISE;369.28,371.12,376.79498,377.835;dark\n372.63498;12-2;loop;RELIEF FEELS / LIKE A REWARD.;AVOID|RELIEF|GUILT|PROMISE;369.28,371.12,376.79498,377.835;dark\n375.35498;12-3;loop;THE LOOP / REPEATS.;AVOID|RELIEF|GUILT|PROMISE;369.28,371.12,376.79498,377.835;dark\n379.675;12-6;switch;MOTIVATED / FOR A MOMENT.;THE FUTURE SELF|THE HARD MOMENT;379.675,382.715\n382.715;12-7;switch;THEN THE HARD / MOMENT RETURNS.;THE PROMISE|BACK TO COMFORT;377.835,384.955\n386.555;12-8;loop;RELIEF IS / NOT CHANGE.;AVOID|RELIEF|GUILT|PROMISE;369.28,371.12,376.79498,377.835\n387.8;12-9;paths;PRACTICED. / NOT PERMANENT.;FEELING STUCK|A DIFFERENT PRACTICE;387.8,395.24;dark\n390.84;13-9;paths;YOU ARE NOT / INCAPABLE.;ONE PRACTICED BEHAVIOR|PRACTICE SOMETHING ELSE;392.2,395.24\n395.24;13-3;paths;PRACTICE / SOMETHING DIFFERENT.;THE OLD RESPONSE|A DIFFERENT CHOICE;392.2,395.24', '400.47999999999996;13-2;focus;NOT 5 AM. / NOT PERFECTION.;NO PERFECT ROUTINE;402.83502\n404.67502;13-3;focus;NOT YOUR / WHOLE LIFE.;NOT ALL AT ONCE;404.67502\n407.315;13-4;focus;START / MUCH SMALLER.;THE NEXT ACTION;407.315\n408.67502;13-5;clock;BEFORE / YOU SCROLL.;10 MIN|WORK FIRST;411.15503,410.99503\n412.195;13-6;stack;SHOES / ON FIRST.;PUT YOUR SHOES ON;414.035\n415.37;13-7;stack;OPEN THE FILE. / DO ONE PIECE.;OPEN THE FILE|THE SMALLEST PIECE;417.05002,418.25\n419.85;13-8;stack;STOP COLLECTING. / START PRACTICING.;INFORMATION|ACTUAL PRACTICE;421.85,423.05002\n424.25;13-9;focus;DISCOMFORT / DOES NOT HAVE TO GO.;DISCOMFORT CAN STAY;424.25;dark\n426.81;14-1;focus;I CAN DO / HARD THINGS.;WITHOUT RUNNING AWAY;428.17;dark\n431.085;14-2;stack;SMALL ACTIONS. / REAL EVIDENCE.;COLLECT EVIDENCE|PROVE IT TO YOURSELF;432.925,434.045']
def local(c,t):
 off=0
 for a,b in c['ranges']:
  if a-.002<=t<b-.002:return off+t-a
  off+=b-a
 return None
for c,p in zip(CLIPS,PLANS):
 c['vo']=sum(b-a for a,b in c['ranges']);c['duration']=c['vo']+2.5;c['scenes']=[]
 for row in p.splitlines():
  q=row.split(';');cues=[]
  for t in map(float,q[5].split(',')):
   z=local(c,t);cues.append(z if z is not None else (-1 if t<c['ranges'][0][0] else c['duration']+1))
  c['scenes'].append(dict(id=len(c['scenes']),start=local(c,float(q[0])),art=q[1],kind=q[2],title=q[3].replace(' / ','\n'),labels=q[4].split('|'),cues=cues,dark=len(q)>6,feature=False,layout='right',chapter=1))
 for j,s in enumerate(c['scenes']):
  s['end']=c['scenes'][j+1]['start'] if j+1<len(c['scenes']) else c['vo'];s['cues']=[s['end']+1 if t>=s['end']-.04 else t for t in s['cues']]
 assert 35<=c['duration']<=55 and all(s['start']<s['end'] for s in c['scenes']);c['starts']=[s['start'] for s in c['scenes']]
grain=np.random.default_rng(321).normal(0,.5,(H,W,1));BG={False:np.clip(np.array(P)[None,None,:]+grain,0,255).astype(np.uint8),True:np.clip(np.array(I)[None,None,:]+grain*.4,0,255).astype(np.uint8)}
@functools.lru_cache(maxsize=8)
def hero(art,dark):
 a,ink,ps=B.hero(art,False,dark);h,w=a.shape[:2];sc=min(830/w,435/h);wh=(round(w*sc),round(h*sc));a=cv2.resize(a,wh,interpolation=cv2.INTER_AREA);ink=cv2.resize(ink,wh,interpolation=cv2.INTER_AREA);ps=[(cv2.resize(p,(max(1,round(p.shape[1]*sc)),wh[1]),interpolation=cv2.INTER_AREA),round(off*sc)) for p,off in ps];return a,ink,ps
def art(f,s,t):
 a,ink,ps=hero(s['art'],s['dark']);h,w=a.shape[:2];r=t-s['start'];u=min(1,max(0,r/(s['end']-s['start'])));x=495-w/2;y=742-h/2;cap=int(w*B.ease((r+.04)/.45));fill=B.ease((r-.08)/.55)
 for j,(p,off) in enumerate(ps):
  n=min(p.shape[1],cap-off)
  if n<=0:continue
  dx=(1-B.spring(r/.6))*28*(1 if s['id']%2 else -1)+(B.ease(u)-.5)*(14 if j==0 else -10);dy=(1-B.spring(max(0,r-j*.06)/.6))*(20 if j==0 else -20)+(B.ease(u)-.5)*(6 if j==0 else -6);B.blit(f,ink[:,off:off+n],x+off+dx,y+dy,1-fill);B.blit(f,p[:,:n],x+off+dx,y+dy,fill)
def dots(f,c,s,t):
 st=c['ranges'][0][0]+t;phase=5 if st>=168.17 else (95 if st>=164.41 else 100);fg=WH if s['dark'] else I;mut=(119,124,128)
 for j in range(100):
  a=B.ease((t-s['start']-j*.001)/.45);col=RC if phase==5 and j>=95 else (mut if phase!=100 else fg);cv2.circle(f,(110+j%10*27,1040+j//10*27),max(1,int(7*a)),col,1 if phase==95 and j>=95 else -1,cv2.LINE_AA)
 a=B.ease((t-max(s['start'],2.24))/.4);B.text(f,str(phase),456,1037,132,RC if phase==5 else fg,390,alpha=a,weight='Black');B.text(f,'EXCITING' if phase==5 else ('ORDINARY' if phase==95 else 'PEOPLE'),456,1212,32,fg,390,alpha=a);B.text(f,'THOUGHT EXPERIMENT',110,1322,24,mut,780)
def native_paths(f,s,t):
 x,y,w=87,1030,790;r=t-s['start'];D=s['end']-s['start'];fg=WH if s['dark'] else I;mut=(155,164,174) if s['dark'] else (114,121,127)
 for j,l in enumerate(s['labels'][:2]):
  a=B.spring((t-s['cues'][j])/.55);yy=y+85+j*144;B.text(f,l,x,yy-73,34,fg,w,alpha=a)
  ps=np.array([(x+15,yy),(x+w-20,yy)] if j==0 else [(x+15,yy),(x+150,yy),(x+300,yy-30),(x+440,yy+20),(x+610,yy),(x+w-20,yy-45)],float);B.path(f,ps,mut if j==0 else RC,4,a,True)
  if a>.8:
   lengths=np.linalg.norm(np.diff(ps,axis=0),axis=1);d=lengths.sum()*(r/max(D,1)*.65+.12)
   for k,L in enumerate(lengths):
    if d<=L:pt=ps[k]+(ps[k+1]-ps[k])*d/max(L,.001);break
    d-=L
   else:pt=ps[-1]
   cv2.circle(f,tuple(pt.astype(int)),11,RC if j else fg,-1,cv2.LINE_AA)
def scene(c,j,t):
 s=c['scenes'][j];r=t-s['start'];fg=WH if s['dark'] else I;f=BG[s['dark']].copy();B.text(f,'WHY WE BECOME',85,119,26,fg,400,weight='Black');B.text(f,c['topic'],534,124,21,RC,350);B.line(f,(85,181),(900,181),(52,61,66) if s['dark'] else (222,231,237),1);sz=86;a=B.glyph(s['title'],sz,fg,805,'Black')
 while a.shape[0]>244 and sz>62:sz-=2;a=B.glyph(s['title'],sz,fg,805,'Black')
 assert a.shape[0]<=260
 en=1 if j==0 else B.spring(r/.42);B.blit(f,a,87,225+(1-en)*17,en);B.line(f,(90,490),(230,490),RC,5,B.ease((r+.05)/.45));art(f,s,t)
 if s['kind']=='dots':dots(f,c,s,t)
 elif s['kind']=='paths':native_paths(f,s,t)
 else:B.diagram(f,s,t,87,1030,790,320)
 B.line(f,(85,1620),(900,1620),(55,62,67) if s['dark'] else (220,230,236),2);B.line(f,(85,1620),(900,1620),RC,4,t/c['duration']);B.text(f,'THINK DEEPER. LIVE BETTER.',85,1672,22,fg,810);return f
end=cv2.imread('assets/subscribe-end-card.jpeg');ew=935;eh=round(end.shape[0]*ew/end.shape[1]);end=cv2.resize(end,(ew,eh),interpolation=cv2.INTER_LANCZOS4)
def frame(c,t):
 if t>=c['vo']:
  f=BG[False].copy();B.text(f,'WHY WE BECOME',85,145,28,I,800,weight='Black');B.text(f,'THINK\nDEEPER.',85,310,100,I,815,weight='Black');x=(W-ew)//2;f[660:660+eh,x:x+ew]=end;B.text(f,'LIVE BETTER.\nBECOME MORE.',85,1265,53,I,815,weight='Black');B.line(f,(90,1508),(900,1508),RC,5,B.ease((t-c['vo']-.2)/.8));a=B.ease((t-c['vo'])/.28);return cv2.addWeighted(scene(c,len(c['scenes'])-1,c['vo']-.001),1-a,f,a,0)
 j=max(0,bisect.bisect_right(c['starts'],t)-1);f=scene(c,j,t);r=t-c['starts'][j]
 if j and r<.18:
  prev=scene(c,j-1,c['starts'][j]-.01);a=B.ease(r/.18)
  if j%3==0 and c['scenes'][j]['dark']==c['scenes'][j-1]['dark']:y=int(H*a);f[y:]=prev[y:];cv2.line(f,(0,y),(W,y),RC,3)
  else:f=cv2.addWeighted(prev,1-a,f,a,0)
 return f
def tm(t):
 v=max(0,round(t*100));h,v=divmod(v,360000);m,v=divmod(v,6000);s,v=divmod(v,100);return f'{h}:{m:02d}:{s:02d}.{v:02d}'
def caption_layout(g):
 lines=[[]];line=''
 for j,w in enumerate(g):
  text=w['punctuated_word'].replace('{','').replace('}','');proposed=(line+' '+text).strip()
  if B.glyph(proposed,60,I,4000).shape[1]>785 and lines[-1]:lines.append([]);line=text
  else:line=proposed
  lines[-1].append(j)
 return lines
def captions(c):
 arr=[];off=0
 for a,b in c['ranges']:
  for w in WORDS:
   if a-.015<=w['start']<b-.025:
    z=dict(w);z['start']=max(off,off+w['start']-a);z['end']=min(off+b-a,off+w['end']-a);arr.append(z)
  off+=b-a
 json.dump(arr,open(O/(c['slug']+'-words.json'),'w'),indent=1)
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat ExtraBold,60,&H00FFFFFF,&H003C62C8,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1.5,2,80,200,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 groups=[];cur=[]
 for w in arr:
  if cur and (len(cur)>=5 or w['start']-cur[-1]['end']>.24 or len(caption_layout(cur+[w]))>2):groups.append(cur);cur=[]
  cur.append(w)
  if re.search(r'[.!?:;…][”\"]?$',w['punctuated_word']):groups.append(cur);cur=[]
 if cur:groups.append(cur)
 events=[]
 for gi,g in enumerate(groups):
  layout=caption_layout(g);assert len(layout)<=2;breaks={row[0] for row in layout[1:]}
  for j,target in enumerate(g):
   start=target['start'];stop=g[j+1]['start'] if j+1<len(g) else min(c['vo'],target['end']+.12,groups[gi+1][0]['start'] if gi+1<len(groups) else c['vo'])
   if stop<=start:continue
   parts=[]
   for k,w in enumerate(g):
    if k in breaks:parts.append('\\N')
    word=w['punctuated_word'].replace('{','').replace('}','');parts.append('{\\c&H003C62C8&}' + word if k==j else '{\\c&H00FFFFFF&}'+word)
   line=' '.join(parts).replace(' \\N ','\\N')
   events.append('Dialogue: 0,'+tm(start)+','+tm(stop)+',Default,,0,0,0,,'+line)
 (O/(c['slug']+'.ass')).write_text(header+'\n'.join(events)+'\n')
 (O/(c['slug']+'-script.md')).write_text('# '+c['title']+'\n\n'+' '.join(w['punctuated_word'] for w in arr)+'\n')
 (O/(c['slug']+'-seo.md')).write_text('# '+c['title']+'\n\nA standalone idea from Why You Want Success But Keep Choosing Comfort. Original narration and supplied illustrations, designed natively for Shorts.\n\nThink deeper. Live better. Become more.\n\n#Shorts #Psychology #Discipline #Procrastination #WhyWeBecome\n\nPinned comment: Which small choice will you make differently today?\n')
def audio(c,vo,sr):
 ps=[]
 for a,b in c['ranges']:
  p=vo[round(a*sr):round(b*sr)].copy();n=min(660,len(p)//2);p[:n]*=np.linspace(0,1,n);p[-n:]*=np.linspace(1,0,n);ps.append(p)
 speech=np.concatenate(ps)
 with wave.open(str(O/(c['slug']+'-narration.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(speech,-.98,.98)*32767).astype('<i2').tobytes())
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(O/(c['slug']+'-narration.wav')),'-c:a','libmp3lame','-b:a','192k',str(O/(c['slug']+'-narration.mp3'))],check=True)
 N=round(c['duration']*sr);v=np.zeros(N,np.float32);v[:len(speech)]=speech;vr=float(np.sqrt(np.mean(speech**2)));t=np.arange(N,dtype=np.float32)/sr;music=np.zeros(N,np.float32)
 for j,fs in enumerate([[220,261.626,329.628],[174.614,220,261.626],[130.813,164.814,196],[196,246.942,293.665]]*3):
  a=j*5.5;b=min(c['duration'],a+7)
  if a>=c['duration']:break
  ix=(t>=a)&(t<b);x=t[ix]-a;en=np.minimum(1,x/.75)*np.minimum(1,(b-t[ix])/.9)
  for f in fs:music[ix]+=en*(np.sin(2*np.pi*f*x)+.18*np.sin(2*np.pi*f*2*x))*.2
 st=round(sr/100);bins=np.pad(v,(0,(-N)%st)).reshape(-1,st);en=np.sqrt(np.mean(bins*bins,1));en=np.convolve((en>vr*.2).astype(float),np.ones(25)/25,'same');duck=np.interp(np.arange(N)/st,np.arange(len(en)),en);music*=vr*.0794/max(float(np.sqrt(np.mean(music**2))),1e-5);music*=1-.72*duck;mix=np.column_stack([v+music,v+music]).astype(np.float32)
 def put(x,t,g):
  k=round(t*sr)
  if k<0:x=x[-k:];k=0
  n=min(len(x),N-k)
  if n>0:mix[k:k+n]+=x[:n,None]*g
 x=np.arange(round(sr*.085))/sr;tick=np.sin(2*np.pi*(950-700*x)*x)*np.exp(-x*65);x=np.arange(round(sr*.24))/sr;wh=np.random.default_rng(31).normal(0,1,len(x));wh=np.convolve(wh,np.ones(5)/5,'same');wh*=np.sin(np.pi*np.minimum(1,x/.24))**2;wh/=max(abs(wh))
 for j,s in enumerate(c['scenes']):
  if j and (s['dark'] or j%3==0):put(wh,s['start']-.075,vr*.15)
  if s['kind'] in ('feed','stack','switch','counter','dots'):
   for q in s['cues']:
    if 0<=q<s['end']:put(tick,q+.015,vr*.1)
 put(tick,c['vo']+.3,vr*.1);n=round(sr*.35);mix[-n:]*=np.linspace(1,0,n)[:,None]
 with wave.open(str(O/(c['slug']+'-raw.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(mix,-.98,.98)*32767).astype('<i2').tobytes())
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(O/(c['slug']+'-raw.wav')),'-af','loudnorm=I=-16:LRA=11:TP=-1.5','-ar','44100',str(O/(c['slug']+'.wav'))],check=True)
def render(c):
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(O/(c['slug']+'.wav')),'-c:a','libmp3lame','-b:a','192k',str(O/(c['slug']+'-audio.mp3'))],check=True)
 f=O/('short-'+c['slug']+'.mp4');p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s','1080x1920','-r','30','-i','-','-i',str(O/(c['slug']+'.wav')),'-vf',f'ass={O/(c["slug"]+".ass")}:fontsdir={B.FONTS}','-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(f)],stdin=subprocess.PIPE)
 try:
  for j in range(math.ceil(c['duration']*30)):
   p.stdin.write(frame(c,j/30).tobytes())
   if j%300==0:print(c['slug'],j,flush=True)
 finally:p.stdin.close()
 assert p.wait()==0;cv2.imwrite(str(O/('thumbnail-'+c['slug']+'.png')),frame(c,1.1))
 for j,s in enumerate(c['scenes']):cv2.imwrite(str(O/'qa'/f'{c["slug"]}-scene{j:02d}.png'),frame(c,min(s['end']-.04,s['start']+max(.55,(s['end']-s['start'])*.7))))
 for j,t in enumerate([1.1,c['vo']*.55,c['vo']-.35,c['vo']+1.2]):subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(t),'-i',str(f),'-frames:v','1',str(O/'qa'/f'{c["slug"]}-actual{j}.png')],check=True)
 pr=json.loads(subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(f)],capture_output=True,text=True,check=True).stdout);s=next(x for x in pr['streams'] if x['codec_type']=='video');d=float(pr['format']['duration']);assert s['width']==W and s['height']==H and s['r_frame_rate']=='30/1' and 35<=d<=55 and abs(d-c['duration'])<.2
 log=subprocess.run(['ffmpeg','-i',str(f),'-af','loudnorm=print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr;ld=json.loads(log[log.rfind('{'):log.rfind('}')+1]);assert -17.5<=float(ld['input_i'])<=-14.5 and float(ld['input_tp'])<=-.8;(O/(c['slug']+'-technical-qa.json')).write_text(json.dumps(dict(probe=pr,loudness=ld),indent=2));return dict(file=f.name,title=c['title'],duration=d,voice_duration=c['vo'],scene_count=len(c['scenes']),loudness=float(ld['input_i']),thumbnail='thumbnail-'+c['slug']+'.png',source_ranges=c['ranges'])
def prepare(c,vo,sr):
 captions(c);audio(c,vo,sr)
 arr=json.load(open(O/(c['slug']+'-words.json')))
 lines=['# '+c['title']+' — panel / audio synchronization','', 'Original narration excerpts; 15 ms edge fades applied without a duration change. Affine timing map rebuilt for the selected source ranges. No speed change or new synthesis.','', '| Scene | Source panel | Speech | Graphic | Start–end | Label cues |','|---|---|---|---|---|---|']
 for j,sc in enumerate(c['scenes']):
  sc['phrase']=' '.join(w['punctuated_word'] for w in arr if sc['start']<=w['start']<sc['end'])
  sc['motion_preflight']={'intent':'clarity and agency','personality':'snappy, controlled','primary':'semantic reveal / transformation','secondary':'ink hero and text settle','ambient':'restrained counter-drift','max_translation_px':60,'primary_elements':1}
  cues=', '.join(f'{l}: {q:.3f}s' if q<sc['end'] else f'{l}: withheld' for l,q in zip(sc['labels'],sc['cues']))
  lines.append(f"| {j} | {sc['art']} | {sc['phrase'].replace('|','/')} | {sc['kind']} | {sc['start']:.3f}–{sc['end']:.3f} | {cues} |")
  t=min(sc['end']-.07,sc['start']+max(.55,(sc['end']-sc['start'])*.75));raw=O/'qa'/f"{c['slug']}-scene{j:02d}-base.png";cv2.imwrite(str(raw),frame(c,t));out=O/'qa'/f"{c['slug']}-scene{j:02d}.png"
  subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(raw),'-vf',f"setpts=PTS+{t}/TB,ass={O/(c['slug']+'.ass')}:fontsdir={B.FONTS},setpts=PTS-STARTPTS",'-frames:v','1',str(out)],check=True)
 (O/(c['slug']+'-timing-review.md')).write_text('\n'.join(lines)+'\n')
 (O/(c['slug']+'-scene-plan.json')).write_text(json.dumps(c['scenes'],indent=2))
 cv2.imwrite(str(O/('thumbnail-'+c['slug']+'.png')),frame(c,1.1))
 json.dump({'title':c['title'],'duration':c['duration'],'voice_duration':c['vo'],'source_ranges':c['ranges'],'word_count':len(arr),'interpolated_words':[w for w in arr if w['alignment']!='matched'],'caption_source':'Original-script words matched against processed long-form audio; timing estimates, not a millisecond-accuracy guarantee'},open(O/(c['slug']+'-alignment-review.json'),'w'),indent=2)
 (O/(c['slug']+'-script.md')).write_text('# '+c['title']+'\n\n'+' '.join(w['punctuated_word'] for w in arr)+'\n')
if __name__=='__main__':
 with wave.open('assets/voiceover.wav','rb') as w:sr=w.getframerate();assert w.getnchannels()==1;vo=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32)/32768
 mode=sys.argv[1] if len(sys.argv)>1 else 'prepare'
 if mode=='prepare':
  for c in CLIPS:prepare(c,vo,sr)
  json.dump([{k:v for k,v in c.items() if k!='starts'} for c in CLIPS],open(O/'scene-plans.json','w'),indent=2)
  print('PREPARATION_COMPLETE',flush=True)
 elif mode=='stills':
  for c in CLIPS:
   for j,t in enumerate([.1,.25,.6,1.1]):cv2.imwrite(str(O/'qa'/f"{c['slug']}-entrance{j}.png"),frame(c,t))
 else:
  idx=int(mode);c=CLIPS[idx];prepare(c,vo,sr);result=render(c)
  (O/(c['slug']+'-manifest.json')).write_text(json.dumps(result,indent=2));print('COMPLETE_PORTRAIT_MASTER',json.dumps(result),flush=True)
