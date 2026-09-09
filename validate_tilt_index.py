"""Check only the revision 3 toothed tilt interface and export fit coupons."""
import json, math
from pathlib import Path
import parametric_mount as m
import Part, MeshPart
V=m.App.Vector
ROOT=Path(__file__).resolve().parent
out=ROOT/'output_freecad'
doc=m.App.openDocument(str(out/'surround_mount.FCStd'))
arm=doc.getObject('Part_2_SwivelArm_Geometry').Shape
cradle=doc.getObject('Part_3_Cradle_Geometry').Shape
wall=doc.getObject('Part_1_WallPlate_Geometry').Shape
report={'tilt_step_deg':m.TILT_STEP_DEG,'teeth':m.TILT_TEETH,
 'tooth_height_mm':m.TILT_TOOTH_HEIGHT,'female_depth_mm':m.TILT_GROOVE_DEPTH,
 'tooth_ring_radii_mm':[m.TILT_RING_INNER,m.TILT_RING_OUTER],
 'nominal_face_gaps_mm':[.3,.3], 'release_translation_from_nominal_mm':.3,
 'release_travel_from_seated_mm':.6,'released_tip_clearance_mm':.15,
 'indexed_angles_deg':[],'mid_step_interference_mm3':{},'released_sweep_samples':0}
def at(angle,shift):
 s=cradle.copy();s.rotate(V(*m.PITCH),V(1,0,0),angle);s.translate(V(shift,0,0));return s
for angle in range(-30,1,5):
 for shift in [0,-.3]:
  s=at(angle,shift);vol=arm.common(s).Volume
  assert vol<1e-3,(angle,shift,vol)
 report['indexed_angles_deg'].append(angle)
for angle in [-27.5,-22.5,-17.5,-12.5,-7.5,-2.5]:
 vol=arm.common(at(angle,-.3)).Volume
 assert vol>1,(angle,vol)
 report['mid_step_interference_mm3'][str(angle)]=vol
# 0.5-degree sweep with teeth fully disengaged: no clevis spreading needed.
for i in range(61):
 angle=-30+i*.5;s=at(angle,.3);vol=arm.common(s).Volume
 assert vol<1e-3,(angle,vol)
 report['released_sweep_samples']+=1
# Same face profiles on two small face-up test discs, each with a 5.3 mm bore.
# Print and fit these before committing to the complete arm/cradle.
coupon_dir=ROOT/'print'/'fit-coupons';coupon_dir.mkdir(exist_ok=True)
female=Part.makeCylinder(22,4).cut(m.primitive(('serrated',(0,0,4),'Z',m.TILT_GROOVE_DEPTH)))
male=Part.makeCylinder(22,4).fuse(m.primitive(('serrated',(0,0,0),'Z',m.TILT_TOOTH_HEIGHT)))
male.rotate(V(0,0,0),V(1,0,0),180);male.translate(V(0,0,4))
for name,s in [('Tilt_Female_Coupon',female),('Tilt_Male_Coupon',male)]:
 s=s.cut(Part.makeCylinder(2.65,8,V(0,0,-1))).removeSplitter()
 assert s.isValid() and len(s.Solids)==1
 s.translate(V(-s.BoundBox.XMin,-s.BoundBox.YMin,-s.BoundBox.ZMin))
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.04,AngularDeflection=.08,Relative=False)
 mesh.write(str(coupon_dir/(name+'.stl')))
report['scope']='Geometric indexing and axial release only. No strength, creep, wear or print-fit qualification.'
(out/'tilt_index_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
