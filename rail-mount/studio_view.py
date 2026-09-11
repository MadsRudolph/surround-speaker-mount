"""Update the room's revised cradle meshes and create an adjustable studio view."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'render'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'dorm_room.blend'))
# Use listener-facing-TV channel labels, identified from fixed rail positions.
renames=[]
for c in [o for o in bpy.data.objects if o.name.endswith(' / AIM CONTROLS')]:
    old=c.name.split(' / ')[0]
    new='Surround_right' if c.matrix_world.translation.y<3.353 else 'Surround_left'
    if old!=new:
        renames.extend((o,o.name.replace(old,new,1)) for o in bpy.data.objects if o.name.startswith(old+' /'))
for i,(o,name) in enumerate(renames):o.name='Channel_rename_'+str(i)
for o,name in renames:o.name=name
rows=json.loads((OUT/'mount_meshes.json').read_text())
cradle=next(r for r in rows if r['name']=='Eris_Cradle')

def cuboid_geometry(bounds):
    vertices=[];faces=[]
    for x0,y0,z0,x1,y1,z1 in bounds:
        k=len(vertices);vertices.extend([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)])
        faces.extend([tuple(k+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
    return vertices,faces

for o in list(bpy.data.objects):
    if o.name.endswith(' / Eris_Cradle'):
        mat=o.data.materials[0];data=bpy.data.meshes.new('Cradle revision 1.1 / spanner access')
        data.from_pydata(cradle['vertices'],[],cradle['faces']);data.materials.append(mat);data.update();o.data=data
    elif ' / side pad' in o.name and max(v.co.y for v in o.data.vertices)-min(v.co.y for v in o.data.vertices)>.15:
        # Retain object transform and create the 36 mm-wide foam tool window.
        vs,fs=cuboid_geometry([(-.003,-.0775,-.0525,.003,-.018,.0525),(-.003,.018,-.0525,.003,.0775,.0525),(-.003,-.018,-.0525,.003,.018,.032)])
        mat=o.data.materials[0];data=bpy.data.meshes.new('Notched side pad');data.from_pydata(vs,[],fs);data.materials.append(mat);data.update();o.data=data
bpy.context.scene['Mount revision']='1.1 — enlarged inner spanner recess; tool-access foam windows.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'dorm_room.blend'))

# Retain one complete hierarchy, so the tested pan/tilt controls still work.
for o in list(bpy.data.objects):
    if not o.name.startswith('Surround_right /'):
        bpy.data.objects.remove(o,do_unlink=True)
scene=bpy.context.scene
control=bpy.data.objects['Surround_right / AIM CONTROLS'];control.matrix_world=Matrix.Identity(4)
control['pan_deg']=-15.;control['tilt_step']=7;control['show_speaker']=True
control.id_properties_ui('show_speaker').update(description='Hide speaker and retaining straps to inspect the cradle and inner bolt recesses.')
hide_terms=['Eris cabinet','front baffle','driver flange','rubber surround','woven cone','dome','rear amplifier panel','rear reflex port','volume knob','power LED','rear socket','fitted webbing loop','strap buckle']
for o in scene.objects:
    if any(' / '+term in o.name for term in hide_terms):
        for prop in ['hide_render','hide_viewport']:
            drv=o.driver_add(prop).driver;drv.type='SCRIPTED'
            var=drv.variables.new();var.name='show';var.targets[0].id=control;var.targets[0].data_path='["show_speaker"]';drv.expression='1-show'

def mat(name,color,rough=.5):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
slate=mat('Studio / charcoal mineral',(.035,.045,.053),.75)
wood=bpy.data.materials.get('Rail / warm beech') or mat('Beech',(.35,.2,.10))
def box(name,loc,size,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
    mod=o.modifiers.new('Edge highlights','BEVEL');mod.width=.002;mod.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL');return o
box('Concrete reference panel',(0,-.09,0),(.40,.10,.40),slate)
box('Actual 50 x 40 mm rail',(0,-.020,0),(.38,.04,.05),wood)
box('Studio floor',(0,.18,-.21),(200,200,.02),slate)
def area(name,loc,target,power,size,color):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Key / large softbox',(.45,.5,.70),(0,.2,0),55,.65,(1,.91,.80))
area('Fill',(-.45,.55,.30),(0,.2,0),22,.55,(.73,.86,1))
area('Edge light',(.35,-.2,.35),(0,.2,0),45,.35,(1,.82,.61))
scene.world=bpy.data.worlds.new('Studio world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.20,.25,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.18
bpy.ops.object.camera_add(location=(.64,.88,.38));camera=bpy.context.object;camera.name='Mount inspection camera';camera.data.lens=52
def aim(loc,target,lens=52):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
aim((.64,.88,.38),(0,.20,-.025));scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=72;scene.cycles.use_denoising=True;scene.view_settings.exposure=0
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    if any(d.type=='OPTIX' for d in prefs.devices):
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
scene.render.resolution_x=1920;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene['Controls']='Select Surround_right / AIM CONTROLS. pan_deg: ±90. tilt_step: 0–12, each 5 degrees down. show_speaker: reveal the cradle.'
scene['Revision']='1.1 engineering prototype, no assigned safe working load.'
control.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT');control.select_set(True);bpy.context.view_layer.objects.active=control
for screen in bpy.data.screens:
    for area_ui in screen.areas:
        if area_ui.type=='VIEW_3D':
            area_ui.spaces.active.region_3d.view_perspective='CAMERA'
        elif area_ui.type=='PROPERTIES':area_ui.spaces.active.context='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mount_inspection.blend'))
scene.render.filepath=str(OUT/'mount-studio.png');bpy.ops.render.render(write_still=True)

# Inspect the bolt recesses with the cabinet removed; same source solids.
control['show_speaker']=False;control['pan_deg']=0.;control['tilt_step']=0
control.update_tag();scene.frame_set(2);bpy.context.view_layer.update()
assert all(o.hide_render for o in scene.objects if ' / Eris cabinet' in o.name)
aim((-.28,.64,.30),(0,.30,-.035),58)
scene.render.filepath=str(OUT/'mount-service.png');bpy.ops.render.render(write_still=True)
control['show_speaker']=True;control['pan_deg']=-15.;control['tilt_step']=7
control.update_tag();scene.frame_set(1);bpy.context.view_layer.update();aim((.64,.88,.38),(0,.20,-.025))
scene.render.filepath=str(OUT/'mount-studio.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mount_inspection.blend'))
print('INSPECTION SCENE SAVED; speaker visibility control verified',flush=True)
