from pathlib import Path
import json,re,difflib,math
R=Path(__file__).parent
script=(R/'prep/script.txt').read_text();draft=json.loads((R/'prep/scene-plan.draft.json').read_text())['scenes']
stt=json.loads((R/'assets/voiceover.json').read_text())['results']['channels'][0]['alternatives'][0]['words']
tl=json.loads((R/'timeline.json').read_text())
def norm(s):
 s=s.lower().replace('’',"'")
 return re.findall(r"[a-z0-9]+(?:'[a-z]+)?",s)
def one(s):
 a=''.join(norm(s));return {'ten':'10','five':'5','thirty':'30','six':'6'}.get(a,a)
expected=[];lineinfo=[];wordpos=0
for line in script.splitlines():
 tokens=norm(line)
 if not tokens:continue
 lineinfo.append(dict(text=line,word_start=wordpos,word_end=wordpos+len(tokens)))
 expected.extend(tokens);wordpos+=len(tokens)
observed=[one(x.get('punctuated_word',x['word'])) for x in stt]
sm=difflib.SequenceMatcher(None,[one(x) for x in expected],observed,autojunk=False)
mapping={}
for block in sm.get_matching_blocks():
 for j in range(block.size):mapping[block.a+j]=block.b+j
unmatched=[i for i in range(len(expected)) if i not in mapping]
# Interpolate only unmatched script words between actual matched spoken neighbors, and log them explicitly.
start=[];end=[];certainty=[]
for i in range(len(expected)):
 if i in mapping:
  w=stt[mapping[i]];start.append(w['start']);end.append(w['end']);certainty.append('matched')
 else:
  before=max([j for j in mapping if j<i],default=-1);after=min([j for j in mapping if j>i],default=len(expected))
  a=stt[mapping[before]]['end'] if before>=0 else 0.0;b=stt[mapping[after]]['start'] if after<len(expected) else tl['vo_end']
  n=after-before-1;k=i-before-1;start.append(a+(b-a)*k/max(n,1));end.append(a+(b-a)*(k+1)/max(n,1));certainty.append('interpolated')
coverage=len(mapping)/len(expected)
report=dict(expected_words=len(expected),observed_words=len(stt),exact_normalized_matches=len(mapping),coverage=coverage,interpolated_words=[dict(index=i,word=expected[i],start=start[i],end=end[i]) for i in unmatched],source='Deepgram Nova-3 on final processed narration; script-aware normalized alignment',warning='Timestamps are estimates, not a guarantee of millisecond accuracy.')
(R/'v2/alignment_report.json').write_text(json.dumps(report,indent=2))
if coverage<.94:raise RuntimeError('Insufficient alignment coverage: '+str(coverage))
for l in lineinfo:l['start']=start[l['word_start']];l['end']=end[l['word_end']-1]
# Each row gives panel/phrase anchors within one semantic chapter; surplus art is intentionally omitted, never evenly cut.
triggers=[
[(1,'You say','A better life'),(2,'More money','More money'),(3,'More freedom','More freedom'),(4,'More confidence','More confidence'),(5,'More discipline','More discipline'),(6,'Maybe you want to build','Something of your own'),(7,'Maybe you want to get','Get in shape'),(8,'Maybe you want to learn','The person you imagine'),(9,'But then','The alarm changes everything')],
[(1,'You know you should work','The work can wait?'),(2,'But you open your phone','One easy detour'),(3,'You know you should exercise','Tomorrow is tempting'),(4,'You know you should start','The project stays unopened'),(5,'cleaning your room','A useful-looking escape'),(6,'You watch another video','Another video'),(7,'You make another plan','Another plan'),(8,'And somehow','The day disappears'),(9,'Then night comes','Tomorrow again')],
[(1,"Because here's",'Not a bad life'),(2,'They choose a comfortable','A comfortable moment'),(3,'eventually become','Moments become a life'),(4,'Think about the last','The important thing'),(5,'A work project','Work still waiting'),(6,'A workout','The workout'),(7,'A difficult conversation','The conversation'),(8,"Or something you've",'The delayed beginning'),(9,'You knew exactly','You already know')],
[(1,"There wasn't",'Research is not the problem'),(2,"You didn't need a new",'No new app required'),(3,"You didn't need another",'No more motivation videos'),(4,'You just needed','Beginning feels uncomfortable'),(5,'You checked your phone','A familiar escape'),(6,'You made coffee','Busywork feels useful'),(7,'You organized','Everything except the task'),(8,'You answered','Busy is not progress'),(9,'But at the end','What feels better now?')],
[(1,'Imagine you have','Two different rewards'),(2,'Scrolling gives','Stimulation now'),(3,'Working out gives','Results later'),(4,'Watching another','Entertainment now'),(5,'Learning a skill','Ability later'),(6,'Ordering something','Excitement now'),(7,'Saving money','Freedom later'),(8,'Staying in bed','Comfort now'),(9,'Getting up','A better future')],
[(1,"But your future can't",'The future cannot pay yet'),(2,'The present is real','The present is tangible'),(3,'The future is only','The future is an idea'),(4,"And that's why",'Wanting and choosing differ'),(5,"You're not necessarily",'The ambition can be sincere'),(6,'You can sincerely','The bigger goal is real'),(7,"You're just making",'Deciding for today')],
[(1,"And there's another",'Practice makes it easier'),(2,'The more often','The repeated choice'),(3,'If you repeatedly','Practice escaping'),(4,'If you constantly','Practice eliminating boredom'),(5,'If you keep quitting','Practice leaving'),(6,'And eventually','The automatic response'),(7,'This is why','Knowing is not doing'),(8,'Because knowing','A goal is not a tolerance'),(9,'and being trained','What it takes')],
[(1,'You can have huge','Ambition without tolerance'),(2,'You can dream','Success without risking failure'),(3,'You can want confidence','Safety versus confidence'),(4,'You can want discipline','Temptation within reach'),(5,'And this is where','The self-blame story'),(6,'But sometimes','Maybe it is not the goal'),(8,'The problem is that','Comfort made too easy')],
[(1,'Think about your phone','Right there'),(2,'One tap','Immediate and effortless'),(3,'Now compare','A very different option'),(4,'You have to sit','Concentration costs effort'),(5,"You're going to be confused",'Confusion is part of practice'),(6,"You're going to be bad",'The imperfect beginning'),(7,'Progress will be slow','No instant applause'),(8,'The reward is almost','Invisible progress'),(9,'Of course','Pleasure now, struggle first')],
[(1,'And this is why','Make discipline easier'),(2,'Sometimes','Change the first step'),(3,'Put your phone','Put the phone elsewhere'),(4,'Remove the apps','Remove the pull'),(5,'Keep your workout','Prepare the clothes'),(6,'Keep the book','Prepare the book'),(7,'Open the project','Prepare the project'),(8,'Make the first','An obvious first step'),(9,'Because if every','Less fighting, more starting')],
[(1,'Because what happens','What if you actually try?'),(2,'What happens if you make','What if nobody watches?'),(3,'What happens if you work','What if results disappoint?'),(4,'What happens if you study','What if you still fail?'),(5,'What happens if you finally','What if you are not ready?'),(6,'So sometimes','Preparation or protection?'),(7,"As long as you haven't started",'Not started, not failed'),(8,"As long as you haven't tried",'Untested possibility'),(9,'Comfort protects','Protection has a cost')],
[(1,'And this creates','The relief cycle'),(2,'You feel temporary','Relief feels like a reward'),(3,'So you avoid','Avoid it again'),(4,'You feel guilty','Then comes guilt'),(5,'You promise','A promise to change'),(6,'You imagine','The motivated future self'),(7,'Then the uncomfortable','The difficult moment returns'),(8,'and you return','Back to comfort'),(9,'Until you start','A practiced behavior can change')],
[(3,"You don't need to suddenly",'You do not need a new life'),(2,"You don't need to wake",'No perfect routine required'),(3,'Start much smaller','Start much smaller'),(4,'When you want to scroll','Before the easy option'),(5,'work for ten','Ten minutes first'),(6,"When you don't feel",'Put the shoes on'),(7,'When you keep delaying','Open the file'),(8,'When you want to learn','Actually practice'),(9,"The goal isn't",'Stay with the discomfort')],
[(1,'Because every time','Collect evidence'),(2,"You said you'd work",'You worked'),(3,"You said you'd exercise",'You exercised'),(4,"You said you'd stop",'You stopped'),(5,'These tiny moments','Tiny is not meaningless'),(6,"They're changing",'Change your self-trust'),(7,'Eventually','Not punishment'),(8,'Because you', 'Stop negotiating'),(9,'You ask','The next step')],
[(1,'Because the truth','A future built by choices'),(2,"It's created",'What you repeat'),(3,'You can want freedom','Comfort can train dependence'),(4,'You can want confidence','Safety can train avoidance'),(5,'You can want success','Easy can train escape'),(6,'And none','Do not make life miserable'),(7,'Rest is important','Rest matters'),(8,'Entertainment is important','Enjoyment matters'),(9,'The problem begins','Comfort as the default')],
[(1,'Because sometimes','Easy now, difficult later'),(2,'And sometimes','Difficult now, easier later'),(3,'Studying','Study instead of scrolling'),(4,'Saving','Save instead of spending'),(5,'Practicing','Practice instead of watching'),(6,'Going to','Go instead of staying'),(7,'Having','Have the conversation'),(8,'Starting','Start and finish'),(9,'These choices','An ordinary different life')],
[(1,'So the next time','Notice this moment'),(2,"don't immediately ask",'Not another motivation hunt'),(3,'Ask something else','What am I choosing?'),(4,'Am I choosing','What I want, or what is easy?'),(5,"Because you don't have",'You can keep your comfort'),(6,"You don't have to become",'Not productivity obsession'),(7,"You don't have to turn",'Not constant struggle'),(8,'You just need','Temporary or permanent?'),(9,'You want success','Willing to do the hard parts')],
[(1,'Because the life','Hidden behind the first step'),(2,"The skill you're",'Not good at it yet'),(3,"The project you're",'A project that might fail'),(4,"The conversation you've",'The conversation waiting'),(5,"The first attempt",'An imperfect first attempt'),(6,'The boring repetition','The work nobody sees'),(7,'And maybe','One different choice'),(8,'Because every time','One decision at a time'),(9,"So don't ask",'What would that person do next?')]
]
# Locate chapter boundaries by preserved exact opening phrases.
chapter_lines=[]
for i,ch in enumerate(draft):
 anchor=ch['opening_phrase'];lo=next(j for j,l in enumerate(lineinfo) if l['text']==anchor)
 chapter_lines.append(lo)
chapter_lines.append(len(lineinfo))
scenes=[];used=set();cue_report=[]
engines=['thought','feed','stack','search','split','timeline','paths','balance','stairs','focus','window','loop','clock','stack','paths','stairs','switch','finish']
for chapter,(ch,row) in enumerate(zip(draft,triggers),1):
 lo,hi=chapter_lines[chapter-1:chapter+1];points=[];previous=lo
 for p,anchor,title in row:
  matches=[j for j in range(previous,hi) if lineinfo[j]['text'].lower().startswith(anchor.lower())]
  if not matches:
   print('unused_anchor',chapter,p,anchor,flush=True);continue
  j=matches[0];points.append((j,p,title));previous=j+1
 if not points or points[0][0]!=lo:points.insert(0,(lo,points[0][1] if points else 1,ch['title']))
 for point,(first,p,title) in enumerate(points):
  last=points[point+1][0] if point+1<len(points) else hi
  # Split long sections at actual spoken line starts, not equal time intervals.
  groups=[];a=first;wordcount=0
  for j in range(first,last):
   wordcount+=lineinfo[j]['word_end']-lineinfo[j]['word_start']
   if wordcount>=25 and j+1<last:groups.append((a,j+1));a=j+1;wordcount=0
  if a<last:groups.append((a,last))
  for segment,(a,b) in enumerate(groups):
   chunk=lineinfo[a:b];s_time=0.0 if not scenes else chunk[0]['start'];e_time=lineinfo[b]['start'] if b<len(lineinfo) else tl['vo_end']
   if e_time-s_time<.25:continue
   art=f'{chapter:02}-{p}';used.add(art)
   kind=engines[chapter-1]
   if kind=='balance':kind='split'
   if kind=='finish':kind='paths' if p<8 else 'stairs'
   if kind=='clock':kind='clock' if p==5 else 'focus'
   if kind=='window' and p>=6:kind='iceberg'
   if kind=='loop':kind='stack' # The full feedback loop is reserved for a feature beat below.
   if chapter==2 and p==9:kind='timeline'
   if chapter==3 and p<=3:kind='stack'
   if chapter==4 and p<4:kind='thought'
   if chapter==7:kind='paths' if p<6 else 'thought'
   if chapter==14:kind='stack' if p<7 else 'focus'
   if chapter==15 and p>=6:kind='switch'
   if chapter==18 and p==9:kind='focus'
   # Spoken line fragments, capped for readability. Exact fragment starts are actual word timestamps.
   texts=[];cues=[]
   selected=chunk if len(chunk)<=3 else [chunk[0],chunk[len(chunk)//2],chunk[-1]]
   maxn=2 if kind in ['split','paths','timeline','window','iceberg','clock','switch'] else 3
   selected=selected[:maxn]
   for l in selected:
    words=l['text'].strip('“”"').replace('...','').split()
    if not words:continue
    t=' '.join(words[:7]);c=start[l['word_start']]
    if c>=e_time:continue
    texts.append(t);cues.append(c)
   if not texts:texts=[title];cues=[s_time]
   if kind=='clock':texts=['10 MINUTES','BEFORE YOU SCROLL'];idx=next((i for i in range(chunk[0]['word_start'],chunk[-1]['word_end']) if expected[i]=='ten'),chunk[0]['word_start']);cues=[start[idx],start[idx]]
   if len(texts)==1 and kind in ['split','paths','timeline','window','iceberg','switch']:kind='thought'
   layout='right' if p%2 else 'left';dark=(chapter in [11,12] and p in [1,5,9]) or (chapter==17 and p==8)
   feat=(chapter,p,segment) in [(3,3,0),(5,1,0),(7,1,0),(12,1,0),(13,5,0),(15,2,0),(18,9,0)]
   scenes.append(dict(id=len(scenes),start=s_time,end=e_time,art=art,kind=kind,title=title if not segment else (' '.join(chunk[0]['text'].replace('...','').strip('“”').split()[:8])),labels=texts,cues=cues,dark=dark,layout=layout,chapter=chapter,feature=feat,phrase='\n'.join(l['text'] for l in chunk),reuse_rationale='Continues the same spoken idea with a new graphic beat' if segment else None))
# Extend to the next verified phrase boundary so there are no holes in coverage.
for i,s in enumerate(scenes):s['end']=scenes[i+1]['start'] if i+1<len(scenes) else tl['vo_end']
# One deliberately designed feature loop for the first complete avoidance / relief / repetition / guilt sequence.
loop_s=[i for i,s in enumerate(scenes) if s['chapter']==12 and s['art'] in ['12-1','12-2','12-3','12-4']]
if loop_s:
 first,last=min(loop_s),max(loop_s);x=scenes[first];x['end']=scenes[last]['end'];x['kind']='loop';x['feature']=True;x['title']='Avoidance rewards itself';x['labels']=['AVOID','RELIEF','REPEAT','GUILT']
 opening=chapter_lines[11];range_end=chapter_lines[12]
 anchors=['You avoid','You feel temporary','So you avoid','You feel guilty'];x['cues']=[next(l['start'] for l in lineinfo[opening:range_end] if l['text'].startswith(a)) for a in anchors]
 x['phrase']='\n'.join(s['phrase'] for s in scenes[first:last+1]);scenes=scenes[:first+1]+scenes[last+1:]
for i,s in enumerate(scenes):s['id']=i
# Only render cues within their scene; future labels are withheld rather than clamped.
for s in scenes:
 valid=[(l,c) for l,c in zip(s['labels'],s['cues']) if s['start']<=c<s['end']]
 if not valid:valid=[(s['title'],s['start'])]
 s['labels']=[v[0] for v in valid];s['cues']=[v[1] for v in valid]
 if s['kind']=='loop' and len(valid)!=4:raise RuntimeError('Incomplete loop cue set')
(R/'v2/scene_plan.json').write_text(json.dumps(scenes,indent=2))
# Captions: steady short phrase chunks, individually active-word colored by spoken estimates.
def ass_time(v):
 cs=round(max(0,v)*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
header='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\nScaledBorderAndShadow: yes\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Caption,Montserrat ExtraBold,58,&H00FFFFFF,&H00FFFFFF,&H0016150F,&H64000000,-1,0,0,0,100,100,0,0,1,4,1.5,2,120,120,82,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
events=[];caption_count=0
for l in lineinfo:
 ids=list(range(l['word_start'],l['word_end']))
 groups=[];current=[]
 from PIL import ImageFont
 font=ImageFont.truetype(str(R/'fonts/Montserrat-ExtraBold.ttf'),58)
 for j in ids:
  proposed=current+[j]
  if current and (len(proposed)>7 or font.getlength(' '.join(expected[k] for k in proposed))>1510):groups.append(current);current=[]
  current.append(j)
 if current:groups.append(current)
 for chunk in groups:
  caption_count+=1
  for active in chunk:
   a=start[active];b=end[active]
   if b-a<.025:continue
   pieces=[]
   for j in chunk:
    token=expected[j];color='&H003C62C8&' if j==active else '&H00FFFFFF&';pieces.append('{\\c'+color+'}'+token)
   events.append(f'Dialogue: 0,{ass_time(a)},{ass_time(b)},Caption,,0,0,0,,'+ ' '.join(pieces))
(R/'v2/captions.ass').write_text(header+'\n'.join(events)+'\n')
chapters=[]
for k,ch in enumerate(draft,1):
 s=next(x for x in scenes if x['chapter']==k);t=int(s['start']);chapters.append(f'{t//60:02}:{t%60:02} {ch["title"]}')
seo=(R/'prep/seo.draft.md').read_text();a=seo.index('## Chapters');b=seo.index('## Tags');seo=seo[:a]+'## Chapters\n\n'+'\n'.join(chapters)+'\n\n'+seo[b:];(R/'v2/seo.md').write_text(seo)
allart=[f'{s:02}-{p}' for s in range(1,19) for p in range(1,10)]
log=['# Panel synchronization review','','Actual scene intervals use final processed narration estimates; no equal-duration image distribution.','']
for s in scenes:log.append(f"- Scene {s['id']:03}: {s['start']:.3f}–{s['end']:.3f}s | {s['art']} | {s['kind']} | {s['title']} | cues {s['cues']} | phrase: {s['phrase'].replace(chr(10),' / ')}")
log+=['','## Panel use inventory']
for art in allart:log.append(f"- {art}: "+('used' if art in {s['art'] for s in scenes} else ('intentionally omitted: generated pseudo-writing' if art=='13-1' else 'intentionally omitted: no separate spoken beat requires it; avoid arbitrary quota cuts')))
(R/'v2/panel_sync_review.md').write_text('\n'.join(log)+'\n')
(R/'v2/line_alignment.json').write_text(json.dumps(lineinfo,indent=2))
print(json.dumps(dict(scenes=len(scenes),used_art=len({s['art'] for s in scenes}),coverage=coverage,narration_seconds=tl['vo_end'],caption_events=len(events),captions=caption_count),indent=2))
