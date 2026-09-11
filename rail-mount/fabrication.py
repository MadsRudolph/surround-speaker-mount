"""Check assembly-tool access, export a tool-fit coupon and a true-size template."""
import os,json,math
os.environ.setdefault('MPLCONFIGDIR','/tmp/rail-mount-matplotlib')
import design as m
import Mesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle

D=m.A.openDocument(str(m.ROOT/'cad'/'eris_rail_mount.FCStd'))
shoe,yoke,cradle=[D.getObject(n+'_Solid').Shape for n in m.NAMES]
report={'revision':'1.1','scope':'Nominal tool-envelope access, not a guarantee for every purchased spanner/socket. Speaker foam must be relieved around the tool opening.','tool_samples':0,'collisions':[]}

def check(label,a,b,tilt,swing):
    if not a.BoundBox.intersect(b.BoundBox):return
    v=a.common(b).Volume
    if v>1e-3:report['collisions'].append(dict(pair=label,tilt=tilt,swing=swing,volume_mm3=v))

# Deliberately solid head envelope: it includes all material surrounding the
# fastener. The target fastener itself is excluded from these obstacle checks.
wrench=m.union([m.cyl(73.4,320,0,15,4,'X'),m.box(73.4,314,0,77.4,326,100)])
for side in [-1,1]:
    tool=wrench.copy()
    if side<0:tool.rotate(m.PITCH,m.V(0,0,1),180)
    for tilt in range(-60,1,5):
        for swing in [-15,0,15]:
            t=tool.copy();t.rotate(m.PITCH,m.V(1,0,0),swing)
            t=m.pose(t,tilt=tilt)
            check('spanner_cradle',t,m.pose(cradle,tilt=tilt),tilt,swing)
            check('spanner_cabinet',t,m.pose(m.cabinet(),tilt=tilt),tilt,swing)
            check('spanner_yoke',t,yoke,tilt,swing)
            report['tool_samples']+=1
report['spanner_envelope']={'head_outer_diameter_mm':30,'thickness_mm':4,'handle_width_mm':12,'handle_reach_from_bolt_mm':100,'handle_swing_deg':[-15,15],'initial_gap_to_speaker_mm':2.9,'recess_diameter_mm':32}
# Outer tilt nut socket, including straight insertion from outside the yoke.
for side in [-1,1]:
    socket=m.cyl(120.1,320,0,10,40,'X')
    if side<0:socket.rotate(m.PITCH,m.V(0,0,1),180)
    for tilt in range(-60,1,5):
        for name,shape in [('cradle',m.pose(cradle,tilt=tilt)),('speaker',m.pose(m.cabinet(),tilt=tilt)),('yoke',yoke)]:
            check('socket_'+name,socket,shape,tilt,0)
report['socket_envelope']={'outer_diameter_mm':20,'length_mm':40,'access':'straight from outside the yoke; target nut excluded'}

# Small section of the actual right-hand cradle pivot. Test with the real bolt,
# 1.6 mm washer and spanner before printing the full cradle.
coupon=cradle.common(m.box(72,285,-35,96,355,35)).removeSplitter()
assert coupon.isValid() and len(coupon.Solids)==1
coupon.rotate(m.V(0,0,0),m.V(0,1,0),90)
b=coupon.BoundBox;coupon.translate(m.V(-b.XMin,-b.YMin,-b.ZMin))
path=m.ROOT/'print'/'fit-coupons'/'Tilt_Bolt_Tool_Access.stl'
mesh=m.MeshPart.meshFromShape(Shape=coupon,LinearDeflection=.06,AngularDeflection=.10,Relative=False);mesh.write(str(path))
reimport=Mesh.Mesh(str(path));assert reimport.isSolid() and reimport.Volume>0
report['tool_coupon']={'closed_solid':True,'volume_mm3':reimport.Volume,'print_bounds_mm':[coupon.BoundBox.XLength,coupon.BoundBox.YLength,coupon.BoundBox.ZLength]}
(m.ROOT/'cad'/'fabrication_validation.json').write_text(json.dumps(report,indent=2))
assert not report['collisions'],report['collisions'][:5]

# A4 landscape, physical page dimensions; no tight bounding box or auto-crop.
fig=plt.figure(figsize=(297/25.4,210/25.4));ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,297),ylim=(0,210));ax.axis('off');ax.set_aspect('equal')
ax.text(15,196,'ERIS RAIL MOUNT / 1:1 CENTRE-MARKING TEMPLATE',fontsize=13,weight='bold')
ax.text(15,187,'Print at 100% / Actual Size. Disable Fit to Page. Check BOTH scale bars before use.',fontsize=9)
for y,label in [(148,'WINDOW-SIDE / RIGHT SURROUND — centre 2646 mm'),(80,'FAR-SIDE / LEFT SURROUND — centre 4060 mm')]:
    x=126
    ax.add_patch(Rectangle((x-90,y-25),180,50,fill=False,lw=.5,linestyle='--'))
    ax.add_patch(Rectangle((x-90,y-23),180,46,fill=False,lw=.8))
    ax.plot([x-96,x+96],[y,y],color='black',lw=.4,linestyle='-.')
    ax.plot([x,x],[y-28,y+28],color='black',lw=.4,linestyle='-.')
    for dx in [-65,65]:
        ax.add_patch(Circle((x+dx,y),1,fill=False,lw=.7))
        ax.plot([x+dx-4,x+dx+4],[y,y],color='black',lw=.6);ax.plot([x+dx,x+dx],[y-4,y+4],color='black',lw=.6)
    ax.text(x,y+28,label,ha='center',fontsize=9,weight='bold')
    ax.text(x,y+13,'130 mm between fixing centres',ha='center',fontsize=9)
    ax.text(x,y-17,'Dashed outline: 50 mm rail height / Solid outline: 46 mm plate',ha='center',fontsize=8)
ax.plot([30,130],[25,25],color='black',lw=1)
for x in range(30,131,10):ax.plot([x,x],[23,27],color='black',lw=.7)
ax.text(80,30,'100 mm horizontal scale check',ha='center',fontsize=8)
ax.plot([253,253],[35,85],color='black',lw=1)
ax.plot([251,255],[35,35],color='black',lw=1);ax.plot([251,255],[85,85],color='black',lw=1)
ax.text(259,60,'50 mm vertical scale check',rotation=90,ha='center',va='center',fontsize=8)
ax.text(15,12,'TRANSFER CENTRES ONLY. Drill diameters, depth and anchors follow the selected concrete-fixing instructions.',fontsize=8)
fig.savefig(m.ROOT/'cad'/'drilling-template-A4-100percent.pdf')
plt.close(fig)
print(json.dumps(report,indent=2),flush=True)
