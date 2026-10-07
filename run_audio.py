from pathlib import Path
import json,re,time,subprocess,concurrent.futures,urllib.request,urllib.parse
R=Path(__file__).parent;C=json.loads((R/'.credentials.json').read_text());KEY=C['DEEPGRAM_API_KEY']
A=R/'audio';A.mkdir(exist_ok=True)
script=(R/'prep/script.txt').read_text()
chunks=[];cur=''
for p in script.split('\n\n'):
 if cur and len(cur)+len(p)>1500:chunks.append(cur);cur=''
 cur+=(('\n\n' if cur else '')+p)
if cur:chunks.append(cur)
assert '\n\n'.join(chunks).split()==script.split()
(A/'tts-chunks.json').write_text(json.dumps(chunks,indent=2))
def request(url,data,ctype='application/json',timeout=240):
 req=urllib.request.Request(url,data=data,headers={'Authorization':'Token '+KEY,'Content-Type':ctype})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as x:return x.read()
 except urllib.error.HTTPError as e:
  raise RuntimeError('Provider HTTP '+str(e.code)+' '+e.read().decode(errors='replace')[:500])
def synth(i):
 dst=A/f'part-{i:02}.mp3'
 if dst.exists() and dst.stat().st_size>1000:return
 for attempt in range(3):
  try:
   data=request('https://api.deepgram.com/v2/speak?model=flux-cole-en&encoding=mp3',json.dumps(dict(text=chunks[i])).encode())
   if len(data)<1000:raise RuntimeError('Unexpected short audio response')
   tmp=dst.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(dst);print('tts_complete',i,len(data),flush=True);return
  except Exception as e:
   print('tts_error',i,str(e)[:500],flush=True)
   if attempt==2:raise
   time.sleep(3*(attempt+1))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(synth,range(len(chunks))))
concat=A/'concat.txt';concat.write_text(''.join(f"file '{A/f'part-{i:02}.mp3'}'\n" for i in range(len(chunks))))
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-ar','48000','-ac','1',str(A/'raw.wav')],check=True)
filters='highpass=f=80,equalizer=f=220:width_type=o:width=1.2:g=2.5,equalizer=f=3500:width_type=o:width=1.5:g=-2.2,equalizer=f=10000:width_type=o:width=1.0:g=1.8,acompressor=threshold=0.12:ratio=3.2:attack=15:release=220,silenceremove=stop_periods=-1:stop_duration=0.4:stop_threshold=-45dB,loudnorm=I=-16:LRA=11:TP=-1.0'
vo=R/'assets/voiceover.wav';subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(A/'raw.wav'),'-af',filters,'-ar','48000','-ac','1',str(vo)],check=True)
dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(vo)]))
print('processed_narration_seconds',dur,flush=True)
aligned=R/'assets/voiceover.json'
if not aligned.exists():
 raw=request('https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&punctuate=true',vo.read_bytes(),'audio/wav')
 aligned.write_bytes(raw)
words=json.loads(aligned.read_text())['results']['channels'][0]['alternatives'][0]['words']
print('stt_words',len(words),'last_word',words[-1]['end'],flush=True)
(R/'timeline.json').write_text(json.dumps({'vo_end':dur,'total':dur+4.0,'end_card_seconds':4.0},indent=2))
print('AUDIO_DONE',flush=True)
