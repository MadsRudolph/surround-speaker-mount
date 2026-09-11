"""Solve room aiming and check end-wall/ceiling clearance for the final layout."""
import json,math
import numpy as np
import design as m
# Solve acoustic axis from an approximate tweeter centre, not cabinet box centre.
# World is Blender: X across room, Y along room, Z up, millimetres.
ear=np.array([350.,3352.974435,1400.])
placements=[]
def acoustic(pan,tilt,along):
    Rz=np.array([[math.cos(pan),-math.sin(pan),0],[math.sin(pan),math.cos(pan),0],[0,0,1]])
    Rx=np.array([[1,0,0],[0,math.cos(tilt),-math.sin(tilt)],[0,math.sin(tilt),math.cos(tilt)]])
    pivot=np.array([0.,135.,0.]);pitch=np.array([0.,320.,0.])
    point=np.array([0.,401.,66.])
    local=pivot+Rz@(pitch+Rx@(point-pitch)-pivot)
    direction=Rz@Rx@np.array([0.,1.,0.])
    # Local +Y is world +X; local +X is world -Y (proper rotation).
    world=np.array([40+local[1],along-local[0],2075+local[2]])
    forward=np.array([direction[1],-direction[0],direction[2]])
    return world,forward
for label,along,guess in [('Surround_right',2646.,76.),('Surround_left',4060.,-76.)]:
    def residual(q):
        p,f=acoustic(q[0],q[1],along);d=ear-p;d/=np.linalg.norm(d)
        return f-d
    q=np.radians([guess,-40])
    for _ in range(20):
        r=residual(q);eps=1e-5
        J=np.column_stack([(residual(q+np.eye(2)[i]*eps)-r)/eps for i in range(2)])
        delta=np.linalg.lstsq(J,-r,rcond=None)[0]
        q=np.clip(q+delta,np.radians([-90,-60]),np.radians([90,0]))
        if np.linalg.norm(delta)<1e-9:break
    pan,tilt=np.degrees(q)
    indexed=round(tilt/5)*5
    p,f=acoustic(math.radians(pan),math.radians(indexed),along)
    d=ear-p;distance=np.linalg.norm(d);d/=distance
    error=math.degrees(math.acos(np.clip(f@d,-1,1)))
    placements.append(dict(name=label,rail_centre_along_room_mm=along,pan_deg=pan,ideal_tilt_deg=tilt,installed_tilt_deg=indexed,tweeter_world_mm=p.tolist(),distance_to_ears_mm=distance,aim_error_deg=error,fixing_along_room_mm=[along-65,along+65]))
# Channel names are from the seated listener facing the modeled TV.
left_direction=np.cross(np.array([0.,0.,1.]),np.array([2313.1,2551.26,1218.3])-ear)
for place in placements:
    side='left' if left_direction@(np.array(place['tweeter_world_mm'])-ear)>0 else 'right'
    assert place['name']=='Surround_'+side
installation={'ear_world_mm':ear.tolist(),'ear_position_is_estimated':True,'tweeter_local_mm':[0,401,66],'tweeter_position_is_approximate':True,'rail_face_world_x_mm':40,'rail_centre_height_mm':2075,'placements':placements}

if __name__=='__main__':
    d=m.A.openDocument(str(m.ROOT/'cad'/'eris_rail_mount.FCStd'))
    parts=[(d.getObject(n+'_Solid').Shape,k) for n,k in zip(m.NAMES,['fixed','yoke','cradle'])]
    parts += [(m.cabinet(),'cradle'),(m.connectors(),'cradle')]
    parts += [(s,k) for n,s,k in m.hardware() if k!='fixed']
    minimum=1e9;failures=[];samples=0
    for place in installation['placements']:
        along=place['rail_centre_along_room_mm']
        for pan in range(-90,91,10):
            for tilt in range(-60,1,5):
                for s,kind in parts:
                    b=m.pose(s,pan,tilt,kind=kind).BoundBox
                    # Room end planes, opposite wall and ceiling; near wall/rail
                    # interference is covered in validate.py.
                    clearances=[along-b.XMax,4400-along+b.XMin,2550-40-b.YMax,2600-2075-b.ZMax,2075+b.ZMin]
                    minimum=min(minimum,*clearances)
                    if min(clearances)<-.001:failures.append([place['name'],pan,tilt,min(clearances)])
                samples+=1
    installation['room_clearance']={'poses_across_two_mounts':samples,'minimum_end_opposite_wall_floor_or_ceiling_clearance_mm':minimum,'collisions':failures,'scope':'Rigid parts, cabinet, connector allowance and moving hardware; room end planes, opposite wall, ceiling and floor.'}
    assert not failures,failures[:5]
    (m.ROOT/'render'/'installation.json').write_text(json.dumps(installation,indent=2))
    report=json.loads((m.ROOT/'cad'/'validation.json').read_text());report['installation']=installation
    (m.ROOT/'cad'/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(installation,indent=2))
