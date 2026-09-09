"""Render a seamless pan/tilt loop from the living-room Blender scene.
blender -b --python showcase/animate_mount.py [-- --preview]
"""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent
PREVIEW='--preview' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(OUT/'living_room.blend'))
scene=bpy.context.scene
base=Matrix.Translation((2.31,3.95,1.55))@Matrix.Rotation(math.pi/2,4,'Z')
Y=Vector((0,.055,.024));P=Vector((0,.110,.024))
def pose(pan,tilt):
    yaw=Matrix.Translation(Y)@Matrix.Rotation(math.radians(pan),4,'Z')@Matrix.Translation(-Y)
    pitch=Matrix.Translation(P)@Matrix.Rotation(math.radians(tilt),4,'X')@Matrix.Translation(-P)
    return yaw,yaw@pitch
oldyaw,oldpitch=pose(28,-10)
def empty(name,parent,loc):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.empty_display_size=.025;return o
root=empty('ANIMATION / wall reference',None,(0,0,0));root.matrix_world=base
pan=empty('ANIMATION / pan ±60 degrees',root,Y)
tilt=empty('ANIMATION / tilt 0 to -30 degrees',pan,P-Y)
bpy.context.view_layer.update()
moving=[]
for o in list(scene.objects):
    if not o.name.startswith('Surround right'):continue
    if o.type!='MESH':continue
    n=o.name
    if any(s in n for s in ['/ Part_1','/ Yaw_',' wall screw',' slim wall cable cover']):continue
    isarm='/ Part_2' in n or '/ Pitch_' in n
    neutral=base@(oldyaw if isarm else oldpitch).inverted()@base.inverted()@o.matrix_world
    o.parent=pan if isarm else tilt
    o.matrix_world=neutral
    moving.append(o)
cable=bpy.data.objects.get('Surround right cable service loop')
scene.frame_start=1;scene.frame_end=96;scene.render.fps=16
levels=[0,-5,-10,-15,-20,-25,-30,-25,-20,-15,-10,-5,0]
def ease(t):return (1-math.cos(math.pi*t))/2
for frame in range(1,98):
    t=(frame-1)/96
    yaw=60*math.sin(2*math.pi*t)
    step=min((frame-1)//8,11)
    phase=((frame-1)-step*8)/8
    if phase<=.25:
        pitch=levels[step];shift=-.3+.6*ease(phase/.25)
    elif phase<=.75:
        pitch=levels[step]+(levels[step+1]-levels[step])*ease((phase-.25)/.5);shift=.3
    else:
        pitch=levels[step+1];shift=.3-.6*ease((phase-.75)/.25)
    tilt.location=P-Y+Vector((shift/1000,0,0))
    tilt.keyframe_insert('location',frame=frame)
    pan.rotation_euler.z=math.radians(yaw);tilt.rotation_euler.x=math.radians(pitch)
    pan.keyframe_insert('rotation_euler',frame=frame);tilt.keyframe_insert('rotation_euler',frame=frame)
    if cable:
        b=cable.data.splines[0].bezier_points[0]
        b.co=base@pose(yaw,0)[0]@Matrix.Translation((shift/1000,0,0))@pose(0,pitch)[1]@Vector((.009,.14,.075))
        b.keyframe_insert('co',frame=frame)
scene.camera=bpy.data.objects['02 — mount in use']
scene.camera.data.lens=48
scene.render.resolution_x=720;scene.render.resolution_y=600;scene.render.resolution_percentage=100
# Keep the entire moving assembly and wall plate in frame at all rendered poses.
subjects=moving+[o for o in scene.objects if o.name.startswith('Surround right / Part_1')]
for attempt in range(30):
    inside=True
    for frame in range(1,97,3):
        scene.frame_set(frame);bpy.context.view_layer.update()
        points=[world_to_camera_view(scene,scene.camera,o.matrix_world@Vector(v)) for o in subjects for v in o.bound_box]
        if not all(.075<p.x<.925 and .075<p.y<.925 for p in points):inside=False;break
    if inside:break
    scene.camera.data.lens*=.97
assert inside,'Animation exceeds camera frame'
# Validate physical attachment and loop closure in world metres.
wall=bpy.data.objects['Surround right / Part_1_WallPlate']
cradle=bpy.data.objects['Surround right / Part_3_Cradle']
speaker=bpy.data.objects['Surround right walnut cabinet']
def matrix_error(a,b):
    return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
scene.frame_set(1);bpy.context.view_layer.update()
fixed=wall.matrix_world.copy();relative=cradle.matrix_world.inverted()@speaker.matrix_world
first=speaker.matrix_world.copy();pivot=pan.matrix_world.translation.copy()
for frame in range(1,98):
    scene.frame_set(frame);bpy.context.view_layer.update()
    assert matrix_error(wall.matrix_world,fixed)<1e-6
    assert matrix_error(cradle.matrix_world@relative,speaker.matrix_world)<1e-5
    assert (pan.matrix_world.translation-pivot).length<1e-6
assert matrix_error(speaker.matrix_world,first)<1e-5
print('VERIFIED: fixed plate and yaw pivot, rigid speaker/cradle, seamless endpoint',flush=True)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.use_persistent_data=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
scene.cycles.device='GPU'
scene.render.image_settings.file_format='PNG'
frames=OUT/'animation-frames';frames.mkdir(exist_ok=True)
scene.frame_set(1)
scene['Animation']='6 second loop, 16 fps; Continuous ±60° yaw; tilt releases axially and re-engages every 5° from 0° to -30°. Fixed wall plate, articulated speaker and cradle. Illustrative cable deformation.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mount_animation.blend'))
selected=[1,25,73] if PREVIEW else range(1,97)
for frame in selected:
    scene.frame_set(frame)
    scene.render.filepath=str(frames/f'{frame:04d}.png')
    bpy.ops.render.render(write_still=True)
print('ANIMATION_COMPLETE',len(selected),'frames',flush=True)
