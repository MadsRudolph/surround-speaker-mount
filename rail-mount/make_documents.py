"""Generate the dimensioned PDF, small tilt-fit coupons and installation diagram."""
import os,json,math
os.environ.setdefault('MPLCONFIGDIR','/tmp/rail-mount-matplotlib')
import design as m
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon,Arc
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
V=m.V

# Isolated samples of the exact new tooth profile; each with the M8 clearance bore.
folder=m.ROOT/'print'/'fit-coupons';folder.mkdir(exist_ok=True)
coupon_report={}
for name,s,angle in [
    ('Female_5deg',m.cyl(-98.5,320,0,32,4,'X').cut(m.teeth(-94.5,.9)),-90),
    ('Male_5deg',m.cyl(-94,320,0,32,4,'X').fuse(m.teeth(-94,.8)),90)]:
    s=s.cut(m.cyl(-101,320,0,4.25,16,'X')).removeSplitter()
    assert s.isValid() and len(s.Solids)==1
    s.rotate(V(0,0,0),V(0,1,0),angle)
    b=s.BoundBox;s.translate(V(-b.XMin,-b.YMin,-b.ZMin))
    mesh=m.MeshPart.meshFromShape(Shape=s,LinearDeflection=.04,AngularDeflection=.08,Relative=False)
    mesh.write(str(folder/(name+'.stl')))
    coupon_report[name]={'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume}
(folder/'validation.json').write_text(json.dumps(coupon_report,indent=2))

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
ink='#243b46';bronze='#b08351';grey='#c8d0d2'
def dim(ax,a,b,label,offset=0):
    ax.annotate('',xy=a,xytext=b,arrowprops={'arrowstyle':'<->','color':ink,'lw':.9})
    ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+offset,label,ha='center',va='bottom',color=ink,fontsize=9,
            bbox={'facecolor':'white','edgecolor':'none','pad':1})
def frame(ax,title):
    ax.set_aspect('equal');ax.axis('off');ax.set_title(title,loc='left',fontweight='bold',color=ink,pad=16)
def footer(fig,page):
    fig.text(.07,.035,'ERIS / THROUGH-RAIL MOUNT     •     mm     •     Prototype: geometric checks only; no assigned working load.',fontsize=8,color=ink)
    fig.text(.93,.035,str(page),ha='right',fontsize=8)

with PdfPages(m.ROOT/'cad'/'mount-drawings.pdf') as pdf:
    fig=plt.figure(figsize=(11.7,8.3));fig.suptitle('Eris E3.5 / concrete-through-rail mount',x=.07,ha='left',fontsize=21,color=ink)
    ax=fig.add_axes([.08,.48,.84,.37]);frame(ax,'01   Fixing interface — front view')
    ax.add_patch(Rectangle((-110,-25),220,50,facecolor='#ead4b7',edgecolor=bronze))
    ax.add_patch(Rectangle((-90,-23),180,46,facecolor='#d7dfe1',edgecolor=ink,lw=1.5))
    for x in [-65,65]:
        ax.add_patch(Circle((x,0),7.1,fc='white',ec=ink));ax.plot([x-10,x+10],[0,0],color=ink,lw=.5);ax.plot([x,x],[-10,10],color=ink,lw=.5)
    dim(ax,(-90,39),(90,39),'180 plate width',2)
    dim(ax,(-65,-40),(65,-40),'130 fixing centres',-1)
    ax.text(0,8,'Both drilling axes on rail centreline',ha='center',fontsize=9)
    ax.text(0,-64,'Rail: 50 high × 40 deep. Plate: 46 high × 12 thick.\nPrinted bores Ø14.2 accept Ø14 / ID11 × 12 metal compression sleeves.\nAnchor body allowance: up to Ø10; washers Ø24 / ID10.5 × 2.',ha='center',va='top',fontsize=9)
    ax.set(xlim=(-130,130),ylim=(-105,65))
    ax=fig.add_axes([.08,.10,.84,.28]);frame(ax,'02   Side arrangement — level reference pose')
    ax.add_patch(Rectangle((-40,-25),40,50,fc='#ead4b7',ec=bronze));ax.add_patch(Rectangle((0,-23),12,46,fc=grey,ec=ink))
    ax.add_patch(Rectangle((12,-30.5),123,16,fc=grey,ec=ink));ax.add_patch(Rectangle((12,14.5),123,16,fc=grey,ec=ink))
    ax.add_patch(Rectangle((239,-105),162,210,fc='#e6ecec',ec=ink))
    ax.add_patch(Rectangle((231,-119),180,10,fc=grey,ec=ink));ax.plot([135,320],[0,0],color=bronze,lw=6)
    for p in [(135,0),(320,0)]:ax.add_patch(Circle(p,4.25,fc='white',ec=ink))
    dim(ax,(0,-145),(135,-145),'135',2);dim(ax,(135,-145),(320,-145),'185 pivot spacing',2)
    ax.text(320,117,'141 W × 162 D × 210 H cabinet',ha='center',fontsize=9)
    ax.text(135,50,'M8 yaw',ha='center',fontsize=9);ax.text(320,30,'Two short M8 tilt bolts',ha='center',fontsize=9)
    ax.set(xlim=(-55,440),ylim=(-165,140));footer(fig,1);pdf.savefig(fig);plt.close(fig)

    fig=plt.figure(figsize=(11.7,8.3));fig.suptitle('Installation / estimated seated listening position',x=.07,ha='left',fontsize=20,color=ink)
    data=json.loads((m.ROOT/'render'/'installation.json').read_text());ax=fig.add_axes([.07,.14,.48,.70]);frame(ax,'03   Room plan — dimensions from STEP')
    ax.add_patch(Rectangle((0,0),2550,4400,fc='#f6f3ed',ec=ink))
    ax.add_patch(Rectangle((83,2353),1200,2000,fc='#b1c4b9',ec=ink));ax.text(683,3353,'BED',ha='center',color=ink)
    ax.add_patch(Rectangle((2243,1992),140,1118,fc=ink));ax.text(2170,2551,'TV',ha='right',color=ink)
    ax.add_patch(Rectangle((0,0),40,4400,fc=bronze));ear=data['ear_world_mm']
    ax.plot(ear[0],ear[1],'o',color='#bd6139');ax.text(ear[0]+110,ear[1]-100,'Ears',color='#bd6139')
    for place in data['placements']:
        p=place['tweeter_world_mm'];a=place['rail_centre_along_room_mm']
        ax.plot([40,p[0]],[a,p[1]],color=bronze,lw=3);ax.plot([p[0],ear[0]],[p[1],ear[1]],'--',color=ink,lw=1)
        ax.plot(p[0],p[1],'s',color=ink,ms=8);ax.text(-60,a,f'{a:.0f}',ha='right',fontsize=9)
    ax.set(xlim=(-350,2650),ylim=(-80,4500))
    text='Reference: window end of the room = 0 mm\n\nRail centre / pivot height: 2075 mm\nRail face projects 40 mm from concrete\n\nMount centres along rail:\n   2646 and 4060 mm from window end\n\nFixing holes along rail:\n   2581, 2711, 3995, 4125 mm\n   all at 2075 mm above modeled floor\n\nStarting aim:\n   window-side +76.10°, far-side −76.10° pan\n   both 55° down (tilt index 11 of 12)\n\nEstimated ears:\n   350 mm from wall\n   3353 mm from window end\n   1400 mm above floor\n\nTweeters approx. 860 mm apart after aiming.\nEar estimate and tweeter location are provisional.\nMeasure from the real room before marking holes.'
    fig.text(.57,.80,text,va='top',fontsize=11,linespacing=1.45,color=ink);footer(fig,2);pdf.savefig(fig);plt.close(fig)

    fig=plt.figure(figsize=(11.7,8.3));fig.suptitle('Assembly / hardware and adjustment',x=.07,ha='left',fontsize=21,color=ink)
    left='PER SPEAKER\n\n1 × Rail Shoe print\n1 × Pan Yoke print\n1 × Eris Cradle print\n\n1 × M8 × 80 hex-head yaw bolt\n2 × M8 × 45 hex-head tilt bolts\n3 × M8 locking nuts\n6 × M8 washers, 1.6 mm thick, Ø16\n\n2 × Ø14 / ID11 × 12 mm metal sleeves\n2 × Ø24 / ID10.5 × 2 mm anchor washers\n2 × concrete fixings (supplier-selected)\n\n2 × 20 mm-wide retaining webbing loops\n    allow about 0.8 m each before trimming\n4 mm base foam, 6 mm side foam\n2 mm front/rear stop pads\n\nNo holes or screws enter the speaker cabinet.'
    right='ASSEMBLY\n\nFit and check the two small tooth coupons first.\nSeat the compression sleeves in the shoe.\nInsert tilt bolt heads from inside the cradle.\nThe two bolts point outwards; there is no through-rod.\nFit inner washers before fitting the cradle to the yoke.\nAdd outer washers and locking nuts.\nJoin yoke to shoe using the M8 × 80 bolt.\nFit pads, speaker and both straps; buckles go on top.\n\nADJUSTMENT\n\nPan: continuous within ±90°; support while adjusting.\nTilt: 0–60° down, in 5° increments.\nSupport speaker, loosen BOTH tilt nuts, slide cradle\n1.0 mm from its seated left position to the right.\nRotate, seat the left teeth, and tighten both nuts.\nDo not ratchet the engaged teeth under load.\n\nThe high-level geometry passes sampled checks.\nAnchor choice, real print fit, sustained-load testing\nand independent overhead retention remain required.'
    fig.text(.08,.82,left,va='top',fontsize=11,linespacing=1.4,color=ink);fig.text(.51,.82,right,va='top',fontsize=10,linespacing=1.4,color=ink)
    footer(fig,3);pdf.savefig(fig);plt.close(fig)
print('Saved mount-drawings.pdf and new 5-degree fit coupons',flush=True)
