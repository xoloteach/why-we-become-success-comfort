from pathlib import Path
import json,shutil
R=Path(__file__).parent
s=(R/'render_motion.reference.py').read_text()
s=s.replace("os.chdir('/data/why-we-become-everyone-else-living-better');cv2.setNumThreads(1)","ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));os.chdir(ROOT);cv2.setNumThreads(1);FONTS=os.path.join(ROOT,'fonts')")
a=s.index('CH=[');b=s.index('\ndef ease',a)
names=[x['title'] for x in json.loads((R/'prep/scene-plan.draft.json').read_text())['scenes']]
s=s[:a]+'CH='+repr(names)+s[b:]
s=s.replace("f'/data/fonts/Montserrat-{weight}.ttf'","f'{FONTS}/Montserrat-{weight}.ttf'")
s=s.replace("(490 if feature else 890)/w,(410 if feature else 610)/h","(490 if feature else 850)/w,(400 if feature else 590)/h")
s=s.replace("if dark and art in ('06-5','01-8','02-9','03-9','09-9'):","if dark: # Intentional paper-cut backing avoids pale-interior / halo faults on obsidian.")
s=s.replace("  if s['art']=='05-9' and len(parts)>1 and j==1:dx+=ease((t-265.9)/1.2)*55\n",'')
s=s.replace("u=r/max(D,1)*.65+.12;px=x+15+u*(w-35);py=yy if kind=='timeline' or i==0 else yy-20*math.sin(u*math.pi*2)","u=min(.86,r/max(D,1)*.65+.12);points=np.array(pts,float);lengths=np.linalg.norm(np.diff(points,axis=0),axis=1);distance=lengths.sum()*u;seg=0\n    while seg<len(lengths)-1 and distance>lengths[seg]:distance-=lengths[seg];seg+=1\n    q=points[seg]+(points[seg+1]-points[seg])*distance/max(lengths[seg],.001);px,py=q")
s=s.replace("if rev[(i+1)%4]>.2:path", "if rev[i]>.2 and rev[(i+1)%4]>.2:path")
a=s.index(" elif kind=='clock':");b=s.index(" elif kind=='switch':",a)
s=s[:a]+''' elif kind=='clock':
  cx=x+120;cy=y+145;a=rev[0];cv2.ellipse(f,(cx,cy),(103,103),-90,0,360*a,RUST,4,cv2.LINE_AA)
  if a>0:
   ang=-math.pi/2+ease((t-cue[0])/1.4)*math.pi/3;line(f,(cx,cy),(cx+67*math.cos(ang),cy+67*math.sin(ang)),fg,5,a);line(f,(cx,cy),(cx,cy-84),fg,3,a)
  text(f,'10 MIN',x+278,y+49,74,RUST,w-278,alpha=a,weight='Black')
  if n>1:text(f,labels[1],x+278,y+166,28,fg,w-278,alpha=rev[1])
''' +s[b:]
s=s.replace("u=ease((r-.9)/.7)","u=ease((t-cue[1])/.7) if len(cue)>1 else 0")
s=s.replace("sz=90 if feat else 82","sz=86 if feat else 78").replace("maxw=1720 if feat else 805","maxw=1720 if feat else 785")
s=s.replace("diagram(f,s,t,660 if feat else tx,502,1150 if feat else 790,320);line", "diagram(f,s,t,660 if feat else tx,502,1150 if feat else 775,320);line")
# Avoid redundant last-card line crossing the canonical brand artwork.
s=s.replace(";line(f,(850,884),(1700,884),RUST,5,ease((t-VO-.5)/1.4))",'')
# The final master is muxed once; render parts without audio to avoid cumulative AAC gaps.
a=s.index(";cmd=['ffmpeg'",s.index("start=float(sys.argv[1])"));b=s.index(';p=subprocess.Popen',a)
s=s[:a]+";cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s','1920x1080','-r','30','-i','-','-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-an','-movflags','+faststart',out]"+s[b:]
s=s.replace("ass=v2/captions.ass:fontsdir=/data/fonts","ass=v2/captions.ass:fontsdir={FONTS}")
(R/'v2/render_motion.py').write_text(s)
(R/'fonts').mkdir(exist_ok=True)
for name in ['Black','ExtraBold','Bold']:shutil.copy('/data/fonts/Montserrat-'+name+'.ttf',R/'fonts'/('Montserrat-'+name+'.ttf'))
# Approved synthesized ambient/SFX bed, with speech ducking at a reduced control rate.
audio=Path('/data/approved-reference/build_audio.py').read_text()
audio=audio.replace("os.chdir('/data/why-we-become-everyone-else-living-better')","os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))").replace("TL = json.load(open('timeline.json'))","TL = json.load(open('timeline.json'))\nSCENES=json.load(open('v2/scene_plan.json'))")
audio=audio.replace("readf32('voiceover.wav')","readf32('assets/voiceover.wav')")
a=audio.index('win = int(0.25 * SR)');b=audio.index('db = -23',a)
audio=audio[:a]+'''step=441
bins=np.pad(vo_full,(0,(-len(vo_full))%step)).reshape(-1,step)
slow=np.sqrt(np.mean(bins*bins,axis=1));slow=np.convolve(slow,np.ones(25)/25,mode='same')
speaking=(slow>speech_rms*.25).astype(np.float32);sm0=np.convolve(speaking,np.hanning(35)/np.hanning(35).sum(),mode='same')
sm=np.interp(np.arange(N,dtype=np.float32)/step,np.arange(len(sm0)),sm0).astype(np.float32)
''' +audio[b:]
a=audio.index("for e in TL['events']:");b=audio.index('put(th, VO_END',a)
audio=audio[:a]+'''for j,sc in enumerate(SCENES):
    if j and (sc['dark'] or j%7==0):put(wh,sc['start']-.12,speech_rms*.13)
    if sc['kind'] in ('feed','stack','loop','search','switch'):
        for cue in sc['cues']:
            if sc['start']<=cue<sc['end']:put(tk,cue+.02,speech_rms*.055)
    if sc['dark'] and j%2==0:put(th,sc['start']+.13,speech_rms*.09)
''' +audio[b:]
audio=audio.replace("'mix_raw.wav'","'v2/mix_raw.wav'").replace('mix_raw.wav -af','v2/mix_raw.wav -af').replace('mix_final.wav\'','v2/mix.wav\'')
(R/'v2/build_audio.py').write_text(audio)
print('adapted_renderer_and_audio')
