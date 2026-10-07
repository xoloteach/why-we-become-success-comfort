from pathlib import Path
import json,hashlib,zipfile
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent
pairs=[(15,35),(23,24),(17,34),(1,4),(14,16),(13,30),(11,26),(8,29),(5,32),(7,36),(3,33),(12,22),(9,18),(2,19),(21,28),(27,38),(6,31),(10,20)]
winners=[35,24,34,4,16,30,26,29,32,36,33,12,18,19,28,27,31,20]
reasons=[
'Stronger detail in preparation tools and book; canonical character retained.',
'Clearer sofa, project and night-to-day storytelling; less enclosing outer border.',
'More deliberate cushion enclosure and cleaner project and doorway compositions.',
'More expressive research overload and busywork; improved action readability.',
'Bolder character scale in phone, practice, parcel and savings contrasts.',
'Clearer present/future choice, open doorway, signpost and bridge metaphors.',
'Clearer walking loop, repeated footprint path and desk avoidance action.',
'Stronger fear, burden, reflection and distraction-room metaphors.',
'Closer expressive views of confusion and practice; clearer unattended progress.',
'Prepared clothing, drawer and bedtime project are more distinctive.',
'Clearer empty shop, failure, unrealized sculpture and protective enclosure.',
'Cohesive relief-to-guilt sequence with clear sunrise and future-self cues.',
'Larger readable character and short-work timer; first checklist cell withheld for pseudo-text.',
'Cleaner completed-action objects and tool readiness; graphics will clarify conceptual evidence.',
'Better separation of healthy rest, game, work-return and repeated-choice metaphors.',
'Clearer difficult path, study, saving, practice and conversation actions.',
'Stronger work/comfort contrast and intentional restorative corner.',
'Stronger inking in skill, project, conversation, repetition and one-stone action.'
]
for d in ['native','layers-draft','qa/crops','selected-sheets','deliverables']: (R/d).mkdir(parents=True,exist_ok=True)
inv=json.loads((R/'input-inventory.json').read_text());byid={x['id']:x for x in inv}
selection=[];report=[];allnative={}

def boundaries(im):
 gray=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY);h,w=gray.shape;xs=[0];ys=[0]
 for fraction in [1/3,2/3]:
  xp=round(w*fraction);lo=max(0,xp-35);hi=min(w,xp+36)
  profile=(gray<100).mean(0);xs.append(int(lo+np.argmax(profile[lo:hi])))
  yp=round(h*fraction);lo=max(0,yp-28);hi=min(h,yp+29)
  profile=(gray<100).mean(1);ys.append(int(lo+np.argmax(profile[lo:hi])))
 xs+=[w];ys+=[h];return xs,ys

def soft_layer(rgb):
 h,w=rgb.shape[:2];edge=np.concatenate([rgb[:5].reshape(-1,3),rgb[-5:].reshape(-1,3),rgb[:,:5].reshape(-1,3),rgb[:,-5:].reshape(-1,3)])
 paper=np.percentile(edge,75,axis=0);dist=np.max(np.abs(rgb.astype(float)-paper),axis=2)
 significant=(dist>30).astype(np.uint8)
 significant=cv2.morphologyEx(significant,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
 count,lab,stats,cent=cv2.connectedComponentsWithStats(significant,8)
 for j in range(1,count):
  if stats[j,cv2.CC_STAT_AREA]<5:significant[lab==j]=0
 # Preserve pale enclosed interiors: fill all holes in the closed foreground mask.
 bg=(1-significant).astype(np.uint8);count,lab,stats,cent=cv2.connectedComponentsWithStats(bg,8)
 borderlabels=set(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]]).tolist())
 interior=~np.isin(lab,list(borderlabels));alpha=np.clip((dist-8)/38,0,1)
 alpha[interior]=1.0;alpha[significant>0]=np.maximum(alpha[significant>0],.8)
 alpha=cv2.GaussianBlur(alpha.astype(np.float32),(3,3),.35)
 rgba=np.dstack([rgb,(alpha*255).astype('uint8')]);yy,xx=np.where(alpha>.12)
 bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)] if len(xx) else [0,0,w,h]
 return rgba,bbox,[float(v) for v in paper]

for s,(candidates,winner,reason) in enumerate(zip(pairs,winners,reasons),1):
 src=R/'input'/f'asset-{winner:02}.jpg';rgb=np.asarray(Image.open(src).convert('RGB'));xs,ys=boundaries(rgb)
 Image.open(src).save(R/'selected-sheets'/f'sheet-{s:02}.jpg',quality=98)
 record={'sheet_id':s,'candidates':list(candidates),'selected_asset':winner,'reason':reason,'selection_method':'editorial comparison of both supplied variants','boundary_x':xs,'boundary_y':ys,'source_original_name':byid[winner]['original_name']}
 selection.append(record)
 board=Image.new('RGB',(1500,900),'#F7F4EE');draw=ImageDraw.Draw(board)
 for p in range(1,10):
  row,col=divmod(p-1,3);cropbox=(xs[col]+7,ys[row]+7,xs[col+1]-7,ys[row+1]-7)
  crop=rgb[cropbox[1]:cropbox[3],cropbox[0]:cropbox[2]].copy()
  # A comparative stronger native cell can replace a cell without replacing a valid whole sheet.
  override={ (8,1):8, (11,6):3, (12,9):22 }.get((s,p))
  actual=winner
  if override:
   actual=override;alternate=np.asarray(Image.open(R/'input'/f'asset-{actual:02}.jpg').convert('RGB'));ax,ay=boundaries(alternate)
   cropbox=(ax[col]+7,ay[row]+7,ax[col+1]-7,ay[row+1]-7);crop=alternate[cropbox[1]:cropbox[3],cropbox[0]:cropbox[2]].copy()
  pid=f'S{s:02}-P{p:02}';Image.fromarray(crop).save(R/'native'/f'{pid}.png');rgba,bbox,paper=soft_layer(crop);Image.fromarray(rgba).save(R/'layers-draft'/f'{pid}.png')
  included=not(s==13 and p==1)
  entry={'panel_id':pid,'source_asset':actual,'source_original_name':byid[actual]['original_name'],'row':row+1,'column':col+1,'crop_box':list(cropbox),'native_dimensions':[crop.shape[1],crop.shape[0]],'bbox':bbox,'estimated_paper':paper,'source_sha256':hashlib.sha256((R/'input'/f'asset-{actual:02}.jpg').read_bytes()).hexdigest(),'use_status':'available_not_yet_rendered' if included else 'intentionally_omitted','omission_reason':None if included else 'AI-generated pseudo-writing on checklist; no replacement generation needed; neighboring action panels cover this beat.','upscale_status':'native_only_neural_reconstruction_pending_network','mask_status':'draft_needs_full_size_dark_and_motion_QA'}
  report.append(entry)
  im=Image.fromarray(crop);im.thumbnail((484,266));x=col*500+(500-im.width)//2;y=row*300+28;board.paste(im,(x,y));draw.text((col*500+12,row*300+8),f'{pid} | asset {actual:02}'+(' | OMIT' if not included else ''),fill='#16150F')
 board.save(R/'qa/crops'/f'selected-{s:02}.jpg',quality=95)
(R/'artwork-selection.json').write_text(json.dumps({'sheets':selection,'thumbnail_candidates':[25,37],'selected_thumbnail':37,'thumbnail_reason':'Stronger facial emotion and sharper right-side focal silhouette while retaining clean left headline space.','unused_variants':'Retained in original input ZIP; intentionally unused alternates, not duplicate production panels.'},indent=2))
(R/'crop-report.json').write_text(json.dumps(report,indent=2))
# Final composed thumbnail: supplied image, manual typography, no AI regeneration.
thumb=Image.open(R/'input'/'asset-37.jpg').convert('RGB').resize((1280,720),Image.Resampling.LANCZOS)
draw=ImageDraw.Draw(thumb);font='/usr/share/fonts/msttcore/ariblk.ttf';small='/usr/share/fonts/msttcore/arialbd.ttf'
draw.text((52,47),'WHY WE BECOME',font=ImageFont.truetype(small,21),fill='#16150F')
for y,t,color in [(182,'COMFORT','#16150F'),(272,'IS COSTING','#C8623C'),(362,'YOU.','#16150F')]:
 size=68;f=ImageFont.truetype(font,size)
 while draw.textlength(t,font=f)>460:size-=1;f=ImageFont.truetype(font,size)
 draw.text((48,y),t,font=f,fill=color,stroke_width=0)
draw.line((52,480,187,480),fill='#C8623C',width=5)
draw.text((52,626),'THE HIDDEN PRICE OF EASY',font=ImageFont.truetype(small,18),fill='#16150F')
thumb.save(R/'deliverables'/'thumbnail.png');thumb.resize((320,180),Image.Resampling.LANCZOS).save(R/'qa'/'thumbnail-mobile.png')
print(json.dumps({'sheet_variants_compared':36,'thumbnail_variants_compared':2,'selected_sheets':18,'native_crops':len(report),'available_panels':sum(x['use_status']!='intentionally_omitted' for x in report),'deliberately_omitted':1,'neural_upscale':'pending_network','thumbnail':'deliverables/thumbnail.png'},indent=2))
