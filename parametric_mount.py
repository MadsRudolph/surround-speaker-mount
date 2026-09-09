"""Run with FreeCAD's Python console or system Python with FreeCAD libraries.
Scripted PartDesign features recompute from Spreadsheet expressions.
Keep this module importable when reopening the FCStd for live editing.
"""
from pathlib import Path
import sys, json
try:
    import FreeCAD as App
except ImportError:
    sys.path.insert(0, '/usr/lib/freecad/lib')
    import FreeCAD as App
import Part
import PartDesign
import Spreadsheet
import MeshPart
# Units: millimetres. X right, Y away from wall, Z up.
DEFAULTS = dict(Speaker_Width=150., Speaker_Depth=150., Speaker_Height=180.,
    Clamp_Padding_Offset=2., Insert_Hole_Diameter=5.6, Wall_Thickness=4.)
NAMES = ['Part_1_WallPlate', 'Part_2_SwivelArm', 'Part_3_Cradle']
YAW = (0.,55.,24.)
PITCH = (0.,110.,24.)

# Revision 3: only the pitch joint indexes; yaw remains a friction swivel.
TILT_STEP_DEG = 5
TILT_TEETH = 72
TILT_RING_INNER = 16.0
TILT_RING_OUTER = 21.0
TILT_GROOVE_DEPTH = 0.50
TILT_TOOTH_HEIGHT = 0.45
TILT_RELEASE_TRAVEL = 0.30  # +X from nominal; 0.15 mm tooth-tip clearance

def serration_mesh(center, axis, height):
    """Closed annular cutter/addition, pointing in -axis, with 72 radial teeth.

    The 0.05 mm backing overlaps the parent body (or lies outside the cutter
    face). Broad tooth crests/valleys occupy 30% of each 5-degree period.
    Female height .50 mm; male .45 mm leaves slight flank/root relief.
    """
    import math
    phases = (0.0, .15, .35, .65, .85)
    levels = (0.0, 0.0, 1.0, 1.0, 0.0)
    vertices = []
    for tooth in range(TILT_TEETH):
        for phase, level in zip(phases, levels):
            a = 2 * math.pi * (tooth + phase) / TILT_TEETH
            for radius, z in [(TILT_RING_INNER, -height*level),
                              (TILT_RING_OUTER, -height*level),
                              (TILT_RING_INNER, .05), (TILT_RING_OUTER, .05)]:
                u, v = radius*math.cos(a), radius*math.sin(a)
                local = (z,u,v) if axis == 'X' else (u,v,z)
                vertices.append(tuple(center[k]+local[k] for k in range(3)))
    faces = []
    count = len(vertices)//4
    for i in range(count):
        a,b,c,d = [4*i+k for k in range(4)]
        e,f,g,h = [4*((i+1)%count)+k for k in range(4)]
        faces.extend([(a,e,f),(a,f,b), (c,d,h),(c,h,g),
                      (a,c,g),(a,g,e), (b,f,h),(b,h,d)])
    return vertices, faces

def geometry(p):
    w,d,h,pad,insert,t = [p[k] for k in DEFAULTS]
    if not (100 <= w <= 200 and 100 <= d <= 200 and 120 <= h <= 240
            and 1 <= pad <= 3 and 4 <= t <= 6 and 5 <= insert <= 6.5):
        raise ValueError('Parameters outside supported geometry envelope; redesign required.')
    parts=[([],[]) for _ in range(3)]
    def box(i,lo,hi,r=1.,cut=False):
        parts[i][int(cut)].append(('box',lo,hi,r))
    def cyl(i,pos,r,length,axis='Z',edge=.4,cut=False):
        parts[i][int(cut)].append(('cyl',pos,r,length,axis,edge))
    # Wall plate; horizontal ears provide the vertical yaw axis.
    box(0,(-45,0,-31),(45,2*t,109),2)
    for z in (0,36):
        box(0,(-22,4,z),(22,55,z+12),1)
        cyl(0,(0,55,z),22,12)
    # Broad root reinforcement, clear of the moving middle knuckle.
    box(0,(-26,4,-14),(26,22,12),2)
    box(0,(-26,4,36),(26,22,62),2)
    cyl(0,(0,55,-2),2.65,52,cut=True,edge=0)
    for x in (-30,30):
        for z in (-16,94):
            cyl(0,(x,-1,z),2.4,2*t+2,'Y',0,True)
            cyl(0,(x,2*t-3,z),5,4,'Y',0,True)
    # 45-degree lead-in chamfers to the counterbores.
    for x in (-30,30):
        for z in (-16,94):
            parts[0][1].append(('cone',(x,2*t-.6,z),4.9,5.6,.7,'Y'))
    # Intermediate arm: 0.3 mm clearance at each friction face.
    cyl(1,(0,55,12.3),22,23.4)
    box(1,(-16,55,16),(16,78,32),2)
    box(1,(-24.3,65,12),(24.3,81,36),2)
    for x in (-24.3,12.3):
        box(1,(x,75,2),(x+12,110,46),1)
        cyl(1,(x,110,24),22,12,'X')
    cyl(1,(0,55,11),2.65,26,cut=True,edge=0)
    cyl(1,(-26,110,24),2.65,52,'X',0,True)
    # Low pitch joint and short rear bridge stay below the terminal panel.
    # Panel lower edge: shelf 10 + foam 2 + cabinet offset 40 = Z52.
    cyl(2,(-12,110,24),22,24,'X')
    box(2,(-12,110,12),(12,143,36),2)
    box(2,(-38,135,12),(38,147,36),2)
    for x in (-38,24):
        box(2,(x,135,6),(x+14,147,34),2)
    inner=w/2+pad+4 # 4 mm reserved for commercial swivel pressure feet.
    side=2*t
    front=145+d+2*pad
    shelf=max(10,2*t)
    box(2,(-inner-side,135,0),(inner+side,front+t,shelf),2)
    box(2,(-inner-side,front,6),(inner+side,front+t,26),1)
    for sign in (-1,1):
        lo,hi=((-inner-side,-inner) if sign<0 else (inner,inner+side))
        box(2,(lo,145,6),(hi,front+t,h*.38),1)
        for y in (145+d*.30,145+d*.75):
            # Boss extends outward; 12 mm depth for a 6 mm long insert.
            x=(-inner-side-4 if sign<0 else inner)
            cyl(2,(x,y,h*.27),10,side+4,'X')
            cyl(2,(x-1,y,h*.27),insert/2,side+6,'X',0,True)
    cyl(2,(-14,110,24),2.65,28,'X',0,True)
    # One toothed face only: the cradle can slide +X into the opposite
    # 0.3 mm cheek gap to disengage, without prying either clevis ear apart.
    # Recessed female face is on the arm's left cheek; raised male face is
    # integral to the cradle's left pitch face. The other face stays flat.
    parts[1][1].append(('serrated',(-12.3,110,24),'X',TILT_GROOVE_DEPTH))
    parts[2][0].append(('serrated',(-12,110,24),'X',TILT_TOOTH_HEIGHT))
    return parts

V=App.Vector
AXES={'X':V(1,0,0),'Y':V(0,1,0),'Z':V(0,0,1)}
def primitive(s):
    if s[0]=='serrated':
        _,center,axis,height=s
        vertices,triangles=serration_mesh(center,axis,height)
        faces=[Part.Face(Part.makePolygon([V(*vertices[i]) for i in tri]+[V(*vertices[tri[0]])])) for tri in triangles]
        shape=Part.makeSolid(Part.makeShell(faces)).removeSplitter()
        if shape.Volume<0: shape.reverse()
        if not shape.isValid(): raise RuntimeError('Invalid serration ring')
        return shape
    if s[0]=='box':
        _,a,b,r=s
        shape=Part.makeBox(*[b[i]-a[i] for i in range(3)], V(*a))
    elif s[0]=='cone':
        _,a,r1,r2,length,axis=s
        return Part.makeCone(r1,r2,length,V(*a),AXES[axis])
    else:
        _,a,radius,length,axis,r=s
        shape=Part.makeCylinder(radius,length,V(*a),AXES[axis])
    if r:
        shape=shape.makeFillet(r,shape.Edges)
    return shape

def solid(spec):
    adds,cuts=spec
    shape=primitive(adds[0])
    for s in adds[1:]: shape=shape.fuse(primitive(s))
    for s in cuts: shape=shape.cut(primitive(s))
    shape=shape.removeSplitter()
    if not shape.isValid() or len(shape.Solids)!=1:
        raise RuntimeError('Invalid/disconnected CAD solid')
    return shape

class MountFeature:
    def __init__(self,obj,index):
        obj.addProperty('App::PropertyInteger','PartIndex','Design').PartIndex=index
        for k in DEFAULTS:
            obj.addProperty('App::PropertyLength',k,'Dimensions')
            obj.setExpression(k,'Parameters.'+k)
        obj.Proxy=self
    def execute(self,obj):
        p={k:getattr(obj,k).Value for k in DEFAULTS}
        obj.Shape=solid(geometry(p)[obj.PartIndex])
    def dumps(self): return None
    def loads(self,state): pass

def build(output=None):
    output=Path(output or Path(__file__).parent/'output_freecad')
    output.mkdir(parents=True,exist_ok=True)
    doc=App.newDocument('SurroundMount')
    sheet=doc.addObject('Spreadsheet::Sheet','Parameters')
    for row,(key,val) in enumerate(DEFAULTS.items(),1):
        sheet.set('A'+str(row),key)
        sheet.set('B'+str(row),str(val)+' mm')
        sheet.setAlias('B'+str(row),key)
    doc.recompute()
    features=[]
    for i,name in enumerate(NAMES):
        body=doc.addObject('PartDesign::Body',name)
        f=body.newObject('PartDesign::FeaturePython',name+'_Geometry')
        MountFeature(f,i)
        body.Tip=f
        features.append(f)
    doc.recompute()
    for f in features:
        if f.Shape.isNull(): raise RuntimeError(f.Name+' failed recompute')
    export(doc,features,output)
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
    return doc

def export(doc,features,output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    report={}
    for f,name in zip(features,NAMES):
        s=f.Shape.copy()
        # Print on X side: bend planes run within layers. Support required.
        s.rotate(V(0,0,0),V(0,1,0),-90 if name=='Part_2_SwivelArm' else 90)
        bb=s.BoundBox
        s.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
        mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.08,
                                    AngularDeflection=.12,Relative=False)
        mesh.write(str(output/(name+'.stl')))
        report[name]={'valid':f.Shape.isValid(),'solids':len(f.Shape.Solids),
            'volume_mm3':f.Shape.Volume,'print_bounds_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength]}
    Part.export(features,str(output/'surround_mount.step'))
    doc.recompute()
    doc.saveAs(str(output/'surround_mount.FCStd'))
    (output/'validation.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':
    # Import by module name so saved Python proxies can be restored later.
    import importlib
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    importlib.import_module('parametric_mount').build()
