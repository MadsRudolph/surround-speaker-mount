"""BRep motion interference and spreadsheet dependency checks; not a load certification."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,'/usr/lib/freecad/lib')
import FreeCAD as App
import Part
import parametric_mount as m
out=Path(__file__).parent/'output_freecad'
doc=App.openDocument(str(out/'surround_mount.FCStd'))
f=[doc.getObject(n+'_Geometry') for n in m.NAMES]
base=[o.Shape.copy() for o in f]
w,d,h,pad=[m.DEFAULTS[k] for k in ('Speaker_Width','Speaker_Depth','Speaker_Height','Clamp_Padding_Offset')]
cab=Part.makeBox(w,d,h,App.Vector(-w/2,145+pad,10+pad))
terminal=Part.makeBox(50,30,70,App.Vector(-25,117,47)) # 5 mm panel margin, provisional 30 mm cable projection
wall=Part.makeBox(1000,30,1000,App.Vector(-500,-30,-500))
results=[]
for pan in range(-60,61,10):
    for tilt in range(-30,1,5):
        arm,cradle,speaker,connector=[s.copy() for s in (base[1],base[2],cab,terminal)]
        for s in (cradle,speaker,connector): s.rotate(App.Vector(*m.PITCH),App.Vector(1,0,0),tilt)
        for s in (arm,cradle,speaker,connector): s.rotate(App.Vector(*m.YAW),App.Vector(0,0,1),pan)
        pairs=[('wallplate_arm',base[0],arm),('arm_cradle',arm,cradle),
               ('wallplate_cradle',base[0],cradle),('wall_speaker',wall,speaker),
               ('wall_cradle',wall,cradle),('speaker_arm',speaker,arm),
               ('speaker_wallplate',speaker,base[0]),('terminal_cradle',connector,cradle),
               ('terminal_arm',connector,arm),('terminal_wallplate',connector,base[0]),('terminal_wall',connector,wall)]
        for label,a,b in pairs:
            vol=a.common(b).Volume
            if vol>1e-3: raise RuntimeError(f'Collision {label} {pan=} {tilt=} {vol=}')
        results.append([pan,tilt])
# Each of the six spreadsheet parameters must propagate and yield valid single solids.
changes={ 'Speaker_Width':160,'Speaker_Depth':160,'Speaker_Height':190,
          'Clamp_Padding_Offset':2.5,'Insert_Hole_Diameter':5.8,'Wall_Thickness':5 }
parameter_tests={}
for row,(key,value) in enumerate(changes.items(),1):
    before=f[2].Shape.Volume
    doc.Parameters.set('B'+str(row),str(value)+' mm')
    doc.recompute()
    after=f[2].Shape.Volume
    assert abs(after-before)>1e-3,(key,before,after)
    assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in f)
    parameter_tests[key]={'test_value_mm':value,'volume_changed':True}
    doc.Parameters.set('B'+str(row),str(m.DEFAULTS[key])+' mm')
    doc.recompute()
report={'collision_free_samples':len(results),'pan_step_deg':10,'tilt_step_deg':5,
        'scope':'Default geometry and speaker envelope; includes provisional 50x70 mm terminal envelope projecting 30 mm; no fasteners, flexible cable, foam or deformation',
        'parameter_recompute':parameter_tests}
(out/'motion_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
App.closeDocument(doc.Name)
