"""BRep interference and print-mesh checks for the rail mount."""
import json,sys,math
from pathlib import Path
import design as m
import Mesh
import numpy as np

V=m.V
doc=m.A.openDocument(str(m.ROOT/'cad'/'eris_rail_mount.FCStd'))
shoe,yoke,cradle=[doc.getObject(n+'_Solid').Shape for n in m.NAMES]
cab=m.cabinet();plug=m.connectors()
report={'scope':'Sampled rigid geometry, nominal fastener envelopes, 50 mm rear connector/port envelope. No strength, wear, creep or flexible cable qualification.', 'collisions':[], 'tilt_index':{},'pan_samples':[], 'pose_samples':0}

def check(label,a,b,pan=None,tilt=None):
    if not a.BoundBox.intersect(b.BoundBox):return
    v=a.common(b).Volume
    if v>1e-3:
        row=dict(pair=label,pan=pan,tilt=tilt,volume_mm3=v)
        report['collisions'].append(row);print('COLLISION',row,flush=True)

# Invariant under pan: evaluate tilt indexing and cabinet clearances once per tilt.
for tilt in range(-60,1,5):
    c=m.pose(cradle,tilt=tilt);s=m.pose(cab,tilt=tilt);p=m.pose(plug,tilt=tilt)
    check('yoke_cradle',yoke,c,tilt=tilt)
    check('yoke_cabinet',yoke,s,tilt=tilt)
    check('yoke_connectors',yoke,p,tilt=tilt)
    check('cradle_cabinet',c,s,tilt=tilt)
    check('cradle_connectors',c,p,tilt=tilt)
    check('seated_teeth',yoke,m.pose(cradle,tilt=tilt,shift=-.5),tilt=tilt)
    for name,hw,kind in m.hardware():
        if name.startswith('Tilt_'):
            check(name+'_speaker',hw,s,tilt=tilt)
            check(name+'_connectors',hw,p,tilt=tilt)
    print('TILT',tilt,flush=True)
report['tilt_index']['indexed_angles_deg']=list(range(-60,1,5))
for tilt in [-57.5,-32.5,-2.5]:
    v=yoke.common(m.pose(cradle,tilt=tilt,shift=-.5)).Volume
    report['tilt_index'][str(tilt)+'_half_step_interference_mm3']=v
    assert v>1,(tilt,v)
for tilt in range(-60,1,2):
    check('released_tilt',yoke,m.pose(cradle,tilt=tilt,shift=.5),tilt=tilt)
report['tilt_index']['released_samples']=31

# Pan sweep versus fixed shoe, wall plane and wooden rail. Rail runs along X.
rail=m.box(-500,-40,-25,500,0,25)
minimum_wall=1e9
for pan in range(-90,91,10):
    y=m.pose(yoke,pan=pan,kind='yoke')
    check('shoe_yoke',shoe,y,pan=pan)
    check('rail_yoke',rail,y,pan=pan)
    for tilt in range(-60,1,5):
        for label,shape in [('cradle',cradle),('cabinet',cab),('connectors',plug)]:
            s=m.pose(shape,pan,tilt)
            # The concrete front is Y=-40; timber front is Y=0 only at Z=±25.
            minimum_wall=min(minimum_wall,s.BoundBox.YMin+40)
            if s.BoundBox.YMin < -40-1e-5:
                report['collisions'].append(dict(pair='concrete_'+label,pan=pan,tilt=tilt))
            check('shoe_'+label,shoe,s,pan,tilt)
            check('rail_'+label,rail,s,pan,tilt)
        report['pose_samples']+=1
    report['pan_samples'].append(pan)
    print('PAN',pan,flush=True)
report['minimum_moving_envelope_to_concrete_mm']=minimum_wall
report['minimum_moving_envelope_to_concrete_mm']=min(minimum_wall,min(m.pose(yoke,pan=a,kind='yoke').BoundBox.YMin+40 for a in range(-90,91,10)))

# Nominal hardware versus moving parts, excluding intentional bolt/bore interfaces.
fixed_hw=m.Part.makeCompound([s for n,s,k in m.hardware() if k=='fixed'])
tilt_hw=m.Part.makeCompound([s for n,s,k in m.hardware() if k=='yoke'])
for pan in range(-90,91,10):
    check('fixed_hardware_yoke',fixed_hw,m.pose(yoke,pan=pan,kind='yoke'),pan)
    check('tilt_hardware_shoe',shoe,m.pose(tilt_hw,pan=pan,kind='yoke'),pan)
    check('tilt_hardware_rail',rail,m.pose(tilt_hw,pan=pan,kind='yoke'),pan)
    for tilt in range(-60,1,5):
        for label,shape in [('cradle',cradle),('cabinet',cab),('connectors',plug)]:
            check('fixed_hardware_'+label,fixed_hw,m.pose(shape,pan,tilt),pan,tilt)
report['hardware_sweep']='Nominal yaw hardware checked against moving parts; tilt hardware against fixed shoe and rail, plus cabinet/connector checks at each tilt.'

# STL closure and size after reimport. CAD alone is not sufficient.
report['print_meshes']={}
for name in m.NAMES:
    mesh=Mesh.Mesh(str(m.ROOT/'print'/f'{name}.stl'))
    report['print_meshes'][name]={'closed_solid':mesh.isSolid(),'facets':mesh.CountFacets,'volume_mm3':mesh.Volume}
    assert mesh.isSolid() and mesh.Volume>0,name

from installation import installation
report['installation']=installation
(m.ROOT/'cad'/'validation.json').write_text(json.dumps(report,indent=2))
(m.ROOT/'render'/'installation.json').write_text(json.dumps(report['installation'],indent=2))
print(json.dumps({'collisions':report['collisions'],'samples':report['pose_samples'],'installation':report['installation']},indent=2),flush=True)
assert not report['collisions'], 'See validation.json'
