"""Create a self-contained FreeCAD posing assembly with native expressions."""
from pathlib import Path
import sys,json
sys.path.insert(0,'/usr/lib/freecad/lib')
import FreeCAD as App
import Part
V=App.Vector
ROOT=Path(__file__).resolve().parent
src=App.openDocument(str(ROOT/'output_freecad/surround_mount.FCStd'))
doc=App.newDocument('InteractiveSpeakerMount')
ctrl=doc.addObject('App::FeaturePython','AimControls')
ctrl.Label='AIM CONTROLS — edit Pan / Tilt below'
ctrl.addProperty('App::PropertyFloatConstraint','Pan','Aiming','Degrees about vertical wall pivot')
ctrl.Pan=(0.,-60.,60.,.1)
ctrl.addProperty('App::PropertyFloatConstraint','Tilt','Aiming','Degrees about horizontal cradle pivot')
ctrl.Tilt=(0.,-30.,0.,.1)
yaw=doc.addObject('App::Part','PanJoint')
yaw.Label='Pan joint — vertical Z axis'
yaw.Placement=App.Placement(V(0,55,24),App.Rotation(V(0,0,1),0))
yaw.setExpression('Placement.Rotation.Angle','AimControls.Pan * 1 deg')
pitch=doc.addObject('App::Part','TiltJoint')
pitch.Label='Tilt joint — local X axis'
yaw.addObject(pitch)
pitch.Placement=App.Placement(V(0,55,0),App.Rotation(V(1,0,0),0))
pitch.setExpression('Placement.Rotation.Angle','AimControls.Tilt * 1 deg')
# Explicit axis assignment survives the zero-angle identity rotation.
yaw.setExpression('Placement.Rotation.Axis.x','0')
yaw.setExpression('Placement.Rotation.Axis.y','0')
yaw.setExpression('Placement.Rotation.Axis.z','1')
pitch.setExpression('Placement.Rotation.Axis.x','1')
pitch.setExpression('Placement.Rotation.Axis.y','0')
pitch.setExpression('Placement.Rotation.Axis.z','0')
for name,parent,origin in [('Part_1_WallPlate',None,V()),('Part_2_SwivelArm',yaw,V(0,55,24)),('Part_3_Cradle',pitch,V(0,110,24))]:
    obj=doc.addObject('PartDesign::Body',name)
    f=obj.newObject('PartDesign::Feature',name+'_Solid')
    shape=src.getObject(name+'_Geometry').Shape.copy()
    shape.translate(-origin)
    f.Shape=shape
    if parent:parent.addObject(obj)
speaker=doc.addObject('Part::Feature','SpeakerEnvelope')
speaker.Label='Speaker 150 × 150 × 180 mm'
speaker.Shape=Part.makeBox(150,150,180,V(-75,37,-12))
pitch.addObject(speaker)
panel=doc.addObject('Part::Feature','TerminalPanel')
panel.Label='Terminal panel — height provisional'
panel.Shape=Part.makeBox(40,.6,60,V(-20,36.5,28))
pitch.addObject(panel)
doc.recompute()
# Verify native expression transforms against independent axis-angle placements.
for pan,tilt in [(0,0),(60,-30),(-60,-30),(25,-12)]:
    ctrl.Pan=pan;ctrl.Tilt=tilt;doc.recompute()
    expected_yaw=App.Placement(V(0,55,24),App.Rotation(V(0,0,1),pan))
    expected_pitch=expected_yaw.multiply(App.Placement(V(0,55,0),App.Rotation(V(1,0,0),tilt)))
    for actual,expected in [(yaw.getGlobalPlacement(),expected_yaw),(pitch.getGlobalPlacement(),expected_pitch)]:
        for point in [V(),V(1,0,0),V(0,1,0),V(0,0,1)]:
            assert (actual.multVec(point)-expected.multVec(point)).Length<1e-7
ctrl.Pan=0;ctrl.Tilt=0;doc.recompute()
path=ROOT/'output_freecad/interactive_assembly.FCStd'
doc.saveAs(str(path))
App.closeDocument(src.Name)
App.closeDocument(doc.Name)
# Reopen without a custom proxy/module: controls must still work.
doc=App.openDocument(str(path));doc.AimControls.Pan=45;doc.AimControls.Tilt=-20;doc.recompute()
expected=App.Placement(V(0,55,24),App.Rotation(V(0,0,1),45)).multiply(App.Placement(V(0,55,0),App.Rotation(V(1,0,0),-20)))
for point in [V(),V(1,0,0),V(0,1,0),V(0,0,1)]:
    assert (doc.TiltJoint.getGlobalPlacement().multVec(point)-expected.multVec(point)).Length<1e-7
App.closeDocument(doc.Name)
print('FREECAD_INTERACTIVE_VERIFIED',path)

# Preserve verified GUI visibility state when regenerating headlessly.
import zipfile
from io import BytesIO
template=ROOT/'output_freecad/interactive_assembly_visible.FCStd'
if template.exists():
    with zipfile.ZipFile(template) as z:
        gui_state=z.read('GuiDocument.xml')
    with zipfile.ZipFile(path) as z:
        entries={name:z.read(name) for name in z.namelist()}
    entries['GuiDocument.xml']=gui_state
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in entries.items():z.writestr(name,data)
