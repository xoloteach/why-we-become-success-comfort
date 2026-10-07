import sys;sys.path.insert(0,'/data/cv_sr')
from pathlib import Path
import json,cv2,numpy as np
R=Path(__file__).parent;cv2.setNumThreads(2)
for d in ['v2/upscaled','v2/layers','v2/qa']:(R/d).mkdir(parents=True,exist_ok=True)
sr=cv2.dnn_superres.DnnSuperResImpl_create();sr.readModel(str(R/'models/FSRCNN_x4.pb'));sr.setModel('fsrcnn',4)
report={};inventory=json.loads((R/'crop-report.json').read_text())
for e in inventory:
 pid=e['panel_id'];s,p=pid.split('-');ss=int(s[1:]);pp=int(p[1:]);key=f'{ss:02}-{pp}'
 a=cv2.imread(str(R/'native'/f'{pid}.png'));b=sr.upsample(a);l=cv2.resize(a,(b.shape[1],b.shape[0]),interpolation=cv2.INTER_LANCZOS4)
 b=cv2.addWeighted(b,.78,l,.22,0);b=cv2.addWeighted(b,1.1,cv2.GaussianBlur(b,(0,0),.8),-.1,0)
 name=f's{ss:02}_p{pp}.png';cv2.imwrite(str(R/'v2/upscaled'/name),b)
 strips=np.concatenate([b[:16].reshape(-1,3),b[-16:].reshape(-1,3),b[:,:16].reshape(-1,3),b[:,-16:].reshape(-1,3)])
 paper=np.percentile(strips,65,axis=0);dist=np.max(abs(b.astype(float)-paper),axis=2);alpha=np.clip((dist-11)/36,0,1).astype(np.float32)
 solid=(alpha>.48).astype(np.uint8)*255;solid=cv2.morphologyEx(solid,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
 ct,_=cv2.findContours(solid,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);filled=np.zeros_like(solid)
 for contour in ct:
  if cv2.contourArea(contour)>100:cv2.drawContours(filled,[contour],-1,255,-1)
 alpha=np.maximum(alpha,cv2.GaussianBlur(filled,(5,5),0)/255)
 count,lab,stats,_=cv2.connectedComponentsWithStats((alpha>.12).astype(np.uint8),8)
 for j in range(1,count):
  if stats[j,cv2.CC_STAT_AREA]<60:alpha[lab==j]=0
 rgba=np.dstack([b,(np.clip(alpha,0,1)*255).astype(np.uint8)]);cv2.imwrite(str(R/'v2/layers'/name),rgba)
 yy,xx=np.where(alpha>.35);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)] if len(xx) else [0,0,b.shape[1],b.shape[0]]
 report[key]=dict(native=list(a.shape[:2][::-1]),upscaled=list(b.shape[:2][::-1]),bbox=box,method='FSRCNN 4x with 22% Lanczos blend and restrained sharpening',source_panel=pid,use_status=e['use_status'])
 print('reconstructed',key,flush=True)
(R/'v2/upscale_report.json').write_text(json.dumps(report,indent=2));print('UPSCALE_DONE',flush=True)
