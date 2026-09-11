"""Eris rail mount, millimetres; X along rail, Y into room, Z up.

Run with system Python and FreeCAD libraries. Does not overwrite revision 3.
An engineering prototype; geometric verification is not a load rating.
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, '/usr/lib/freecad/lib')
import FreeCAD as A
import Part, MeshPart

ROOT = Path(__file__).resolve().parent
V = A.Vector
YAW = V(0, 135, 0)
PITCH = V(0, 320, 0)
WIDTH, DEPTH, HEIGHT = 141., 162., 210.
NAMES = ['Rail_Shoe', 'Pan_Yoke', 'Eris_Cradle']

def box(x0,y0,z0,x1,y1,z1,r=0):
    s=Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
    return s.makeFillet(r,s.Edges) if r else s

def cyl(x,y,z,r,length,axis='Z'):
    return Part.makeCylinder(r,length,V(x,y,z),{'X':V(1,0,0),'Y':V(0,1,0),'Z':V(0,0,1)}[axis])

def union(shapes):
    s=shapes[0]
    for b in shapes[1:]: s=s.fuse(b)
    return s.removeSplitter()

def teeth(x,height):
    """72 radial teeth, 5 degree pitch; relief projects toward -X."""
    vertices=[]
    for tooth in range(72):
        for phase,level in [(0,0),(.15,0),(.35,1),(.65,1),(.85,0)]:
            a=2*math.pi*(tooth+phase)/72
            for radius,offset in [(22,-height*level),(30,-height*level),(22,.05),(30,.05)]:
                vertices.append(V(x+offset,320+radius*math.cos(a),radius*math.sin(a)))
    faces=[];count=len(vertices)//4
    for i in range(count):
        a,b,c,d=[4*i+k for k in range(4)];e,f,g,h=[4*((i+1)%count)+k for k in range(4)]
        for tri in [(a,e,f),(a,f,b),(c,d,h),(c,h,g),(a,c,g),(a,g,e),(b,f,h),(b,h,d)]:
            faces.append(Part.Face(Part.makePolygon([vertices[j] for j in tri]+[vertices[tri[0]]])))
    s=Part.makeSolid(Part.makeShell(faces)).removeSplitter()
    if s.Volume<0:s.reverse()
    return s

def shapes():
    # 46 mm plate entirely fits the rail's 50 mm face. Two concrete fixing axes.
    shoe=[box(-90,0,-23,90,12,23,2)]
    for z0,z1 in [(-30.5,-14.5),(14.5,30.5)]:
        shoe += [box(-26,4,z0,26,135,z1,1.5),cyl(0,135,z0,26,z1-z0)]
        # Broad roots reinforce both ears without occupying the yaw sweep.
        shoe += [box(-33,4,z0,33,39,z1,1)]
    shoe=union(shoe).cut(cyl(0,135,-32,4.25,64))
    for x in [-65,65]:shoe=shoe.cut(cyl(x,-1,0,7.1,15,'Y'))

    # The U-shaped yoke clears the cabinet and a 50 mm rear connector allowance.
    yoke=[cyl(0,135,-14,26,28),box(-110.5,116,-14,110.5,149,14,2)]
    for x0,x1 in [(-110.5,-94.5),(94.5,110.5)]:
        yoke += [box(x0,131,-14,x1,320,14,2),cyl(x0,320,0,32,x1-x0,'X')]
    yoke=union(yoke).cut(cyl(0,135,-16,4.25,32))
    for x in [-112,93]:yoke=yoke.cut(cyl(x,320,0,4.25,20,'X'))
    yoke=yoke.cut(teeth(-94.5,.9))

    # Shelf bears weight; two webbing loops positively retain the cabinet.
    cradle=[box(-84.5,231,-119,84.5,411,-109,1.5),
            box(-84.5,231,-114,84.5,237,-65,1),
            box(-84.5,403,-114,84.5,411,-88,1)]
    for x0,x1 in [(-84.5,-76.5),(76.5,84.5)]:
        cradle += [box(x0,234,-114,x1,409,12,1.5)]
    for x0 in [-94,80]:cradle += [cyl(x0,320,0,32,14,'X')]
    cradle=union(cradle).fuse(teeth(-94,.8))
    for x0 in [-96,72]:cradle=cradle.cut(cyl(x0,320,0,4.25,25,'X'))
    # Revision 1.1: open 32 mm tool recesses let a 4 mm-thick spanner
    # counterhold the inner hex heads. The handle exits above the side wall.
    # The M8 bearing bore and outer 14 mm pivot disc are unchanged.
    cradle=cradle.cut(cyl(-80,320,0,16,8,'X'))
    cradle=cradle.cut(cyl(72,320,0,16,8,'X'))
    # Two shallow webbing channels on the underside, at y=262 and 376.
    for y in [262,376]:cradle=cradle.cut(box(-86,y-11,-120,86,y+11,-117.8))
    result=[s.removeSplitter() for s in [shoe,yoke,cradle]]
    for name,s in zip(NAMES,result):
        assert s.isValid() and len(s.Solids)==1,(name,s.isValid(),len(s.Solids))
    return result

def cabinet(): return box(-70.5,239,-105,70.5,401,105)

def connectors():
    # Conservative full-width rear panel/plug and port allowance, no cable loops.
    return box(-65,189,-60,65,239,96)

def pose(shape,pan=0,tilt=0,kind='cradle',shift=0):
    s=shape.copy()
    if kind=='cradle':
        s.rotate(PITCH,V(1,0,0),tilt)
        s.translate(V(shift,0,0))
    if kind!='fixed':s.rotate(YAW,V(0,0,1),pan)
    return s

def hardware():
    """Nominal shanks, head/washer/nut envelopes; threads not modeled."""
    rows=[]
    def add(name,s,kind):rows.append((name,s,kind))
    # Yaw M8x80. Washer -> ear -> moving knuckle -> ear -> washer -> nut.
    add('Yaw_M8_shank',cyl(0,135,-32.1,4,80),'fixed')
    add('Yaw_M8_head',cyl(0,135,-37.4,7.5,5.3),'fixed')
    for z in [-32.1,30.5]:
        add('Yaw_washer_'+str(z),cyl(0,135,z,8,1.6).cut(cyl(0,135,z-.1,4.25,2)),'fixed')
    add('Yaw_locknut',cyl(0,135,32.1,7.5,8),'fixed')
    # Separate outward-facing tilt bolts. No rod passes through the speaker.
    for side in [-1,1]:
        parts=[('shank',cyl(78.4,320,0,4,45,'X')),
               ('head',cyl(73.1,320,0,7.5,5.3,'X')),
               ('inner_washer',cyl(78.4,320,0,8,1.6,'X').cut(cyl(78.3,320,0,4.25,2,'X'))),
               ('outer_washer',cyl(110.5,320,0,8,1.6,'X').cut(cyl(110.4,320,0,4.25,2,'X'))),
               ('locknut',cyl(112.1,320,0,7.5,8,'X'))]
        for n,s in parts:
            if side<0:s.rotate(V(0,320,0),V(0,0,1),180)
            add('Tilt_'+str(side)+'_'+n,s,'yoke')
    for x in [-65,65]:
        add('Compression_sleeve_'+str(x),cyl(x,0,0,7,12,'Y').cut(cyl(x,-1,0,5.5,14,'Y')),'fixed')
        add('Anchor_washer_'+str(x),cyl(x,12,0,12,2,'Y').cut(cyl(x,11,0,5.25,4,'Y')),'fixed')
        add('Concrete_fixing_axis_'+str(x),cyl(x,-126,0,3.5,140,'Y'),'fixed')
        add('Concrete_fixing_head_'+str(x),cyl(x,14,0,7.5,5,'Y'),'fixed')
    return rows

def mesh_json(s):
    vs,fs=s.tessellate(.18)
    return {'vertices':[[v.x,v.y,v.z] for v in vs],'faces':fs}

def build():
    for folder in ['cad','print','render']:(ROOT/folder).mkdir(exist_ok=True)
    doc=A.newDocument('Eris_Rail_Mount')
    ss=shapes();report={};render=[];features=[]
    for i,(name,s) in enumerate(zip(NAMES,ss)):
        o=doc.addObject('PartDesign::Body',name)
        f=o.newObject('PartDesign::Feature',name+'_Solid');f.Shape=s
        f.addProperty('App::PropertyString','DesignNote').DesignNote='Regenerate with rail-mount/design.py; prototype, no assigned working load.'
        features.append(f)
        ps=s.copy()
        # Bending plane in layers, tooth interfaces face up. Supports required.
        ps.rotate(V(0,0,0),V(0,1,0),-90 if i==1 else 90)
        b=ps.BoundBox;ps.translate(V(-b.XMin,-b.YMin,-b.ZMin))
        mesh=MeshPart.meshFromShape(Shape=ps,LinearDeflection=.06,AngularDeflection=.10,Relative=False)
        mesh.write(str(ROOT/'print'/f'{name}.stl'))
        report[name]={'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume,
                     'print_dimensions_mm':[ps.BoundBox.XLength,ps.BoundBox.YLength,ps.BoundBox.ZLength]}
        render.append({'name':name,'kind':['fixed','yoke','cradle'][i],**mesh_json(s)})
    for name,s,kind in hardware():
        f=doc.addObject('PartDesign::Feature',name.replace('-','m').replace('.','p'));f.Shape=s
        render.append({'name':name,'kind':kind,'hardware':True,**mesh_json(s)})
    c=doc.addObject('PartDesign::Feature','Speaker_Envelope');c.Shape=cabinet()
    c.addProperty('App::PropertyString','Dimensions').Dimensions='141 W x 162 D x 210 H mm'
    doc.recompute();doc.saveAs(str(ROOT/'cad'/'eris_rail_mount.FCStd'))
    Part.export(features,str(ROOT/'cad'/'eris_rail_mount.step'))
    (ROOT/'cad'/'geometry_validation.json').write_text(json.dumps(report,indent=2))
    (ROOT/'render'/'mount_meshes.json').write_text(json.dumps(render,separators=(',',':')))
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':build()
