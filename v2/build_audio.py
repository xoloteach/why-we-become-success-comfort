import json, os, subprocess, wave
import numpy as np
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
SR = 44100
TL = json.load(open('timeline.json'))
SCENES=json.load(open('v2/scene_plan.json'))
TOTAL, VO_END = TL['total'], TL['vo_end']
N = int(TOTAL * SR) + SR
def ff(cmd): subprocess.run(cmd, shell=True, check=True)
def readf32(path):
    raw = subprocess.run(f'ffmpeg -loglevel error -i {path} -f f32le -ac 1 -ar {SR} -', shell=True, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

# ---- sfx via ffmpeg synth (generated locally = no licensing issues) ----
os.makedirs('sfx', exist_ok=True)
ff('ffmpeg -y -loglevel error -f lavfi -i "anoisesrc=d=1.1:c=pink:r=44100:a=0.9" -af "highpass=f=250,lowpass=f=5200,tremolo=f=3:d=0.2,afade=t=in:d=0.55,afade=t=out:st=0.55:d=0.55" sfx/whoosh.wav')
ff('ffmpeg -y -loglevel error -f lavfi -i "sine=f=1318:d=0.35:r=44100" -af "afade=t=out:st=0.02:d=0.33,volume=0.8" sfx/tick.wav')
ff('ffmpeg -y -loglevel error -f lavfi -i "sine=f=196:d=1.6:r=44100" -af "afade=t=in:d=0.05,afade=t=out:st=0.1:d=1.5,volume=0.9" sfx/thud.wav')
wh, tk, th = readf32('sfx/whoosh.wav'), readf32('sfx/tick.wav'), readf32('sfx/thud.wav')

vo = readf32('assets/voiceover.wav')
vo_full = np.zeros(N, np.float32); vo_full[:len(vo)] = vo[:N]
speech_rms = float(np.sqrt(np.mean(vo ** 2)))
print('vo rms', speech_rms, flush=True)

# ---- ambient pad bgm (Am - F - C - G), synthesized ----
t = np.arange(N, dtype=np.float32) / SR
chords = [[220.00, 261.63, 329.63, 440.00], [174.61, 220.00, 261.63, 349.23], [261.63, 329.63, 392.00, 523.25], [196.00, 246.94, 293.66, 392.00]]
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
SEG = 8.0; XF = 3.0
nseg = int(TOTAL / SEG) + 2
for s in range(nseg):
    ch = chords[s % 4]; t0 = s * SEG - XF / 2; t1 = (s + 1) * SEG + XF / 2
    i0, i1 = max(int(t0 * SR), 0), min(int(t1 * SR), N)
    if i1 <= i0: continue
    tt = t[i0:i1]; env = np.minimum(np.clip((tt - t0) / XF, 0, 1), np.clip((t1 - tt) / XF, 0, 1))
    env = np.sin(env * np.pi / 2) ** 2
    l = np.zeros_like(tt); r = np.zeros_like(tt)
    for k, f in enumerate(ch):
        for det, pan in ((-0.6, 0.35), (0.0, 0.5), (0.7, 0.65)):
            ph = k * 1.7 + det
            sig = np.sin(2 * np.pi * (f + det) * tt + ph) + 0.25 * np.sin(2 * np.pi * 2 * (f + det) * tt + ph)
            sig *= 0.5 + 0.5 * np.sin(2 * np.pi * (0.07 + 0.02 * k) * tt + k)
            l += sig * (1 - pan); r += sig * pan
    sub = np.sin(2 * np.pi * (ch[0] / 2) * tt) * 1.2
    l += sub; r += sub
    L[i0:i1] += l * env; R[i0:i1] += r * env
pad = (L + R) / 2
pad /= (np.sqrt(np.mean(pad ** 2)) + 1e-9)
# gentle pulse for movement
pad *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 4.0)

# ---- ducking envelope from voice ----
step=441
bins=np.pad(vo_full,(0,(-len(vo_full))%step)).reshape(-1,step)
slow=np.sqrt(np.mean(bins*bins,axis=1));slow=np.convolve(slow,np.ones(25)/25,mode='same')
speaking=(slow>speech_rms*.25).astype(np.float32);sm0=np.convolve(speaking,np.hanning(35)/np.hanning(35).sum(),mode='same')
sm=np.interp(np.arange(N,dtype=np.float32)/step,np.arange(len(sm0)),sm0).astype(np.float32)
db = -23 + (1 - sm) * 6           # -23 dB under speech, -17 dB in pauses (rel. voice RMS)
out_ramp = np.clip((t - VO_END) / 1.5, 0, 1)
db = db * (1 - out_ramp) + (-10) * out_ramp
gain = speech_rms * 10 ** (db / 20)
fade = np.clip(t / 3.0, 0, 1) * np.clip((TOTAL - t) / 3.0, 0, 1)
bgm = pad * gain * fade

# ---- sfx placement ----
sfx = np.zeros(N, np.float32)
def put(sig, at, g):
    i = int(max(at, 0) * SR); j = min(i + len(sig), N)
    if j > i: sfx[i:j] += sig[:j - i] * g
for j,sc in enumerate(SCENES):
    if j and (sc['dark'] or j%7==0):put(wh,sc['start']-.12,speech_rms*.13)
    if sc['kind'] in ('feed','stack','loop','search','switch'):
        for cue in sc['cues']:
            if sc['start']<=cue<sc['end']:put(tk,cue+.02,speech_rms*.055)
    if sc['dark'] and j%2==0:put(th,sc['start']+.13,speech_rms*.09)
put(th, VO_END + 0.1, speech_rms * 0.5)

mix = (vo_full + bgm + sfx)[:int(TOTAL * SR)]
peak = float(np.max(np.abs(mix)))
print('mix peak', peak, flush=True)
mix = mix / max(peak, 1.0) * 0.95 if peak > 0.95 else mix
with wave.open('v2/mix_raw.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
ff('ffmpeg -y -loglevel error -i v2/mix_raw.wav -af "loudnorm=I=-16:LRA=11:TP=-1.5" -ar 44100 -ac 2 v2/mix.wav')
print('done', flush=True)
