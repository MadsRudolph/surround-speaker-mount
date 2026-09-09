"""Blender product showcase using the original, unmodified mount meshes.
Run: blender -b --python showcase/render_living_room.py -- --preview
Units: metres. Speakers are illustrative 150 x 150 x 180 mm cabinets.
"""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'showcase'
PREVIEW='--preview' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output_blender/surround_mount.blend'))
source=bpy.context.scene
source.frame_set(1)
for obj in source.objects:
    obj.animation_data_clear()
bpy.context.view_layer.update()
original=[(o.name,o.data.copy(),o.matrix_world.copy()) for o in source.objects if o.type=='MESH' and not o.name.startswith(('Speaker_envelope','Terminal_panel'))]
scene=bpy.data.scenes.new('Living room — surround mount in use')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1

def mat(name,color,rough=.5,metal=0,texture=None):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if texture:
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=texture
        tex.inputs['Detail'].default_value=3
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.001
        l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m
plaster=mat('Warm mineral plaster',(.65,.61,.53),.85,texture=120)
oak=mat('Natural oiled oak',(.34,.19,.083),.48,texture=35)
walnut=mat('Speaker walnut veneer',(.16,.067,.028),.36,texture=70)
# Directional veneer grain: stretched noise with subtle colour and relief.
for wood,light,dark in [(oak,(.40,.25,.12,1),(.25,.13,.055,1)),(walnut,(.20,.09,.037,1),(.085,.030,.010,1))]:
    n=wood.node_tree.nodes;l=wood.node_tree.links;p=n.get('Principled BSDF')
    tc=n.new('ShaderNodeTexCoord');stretch=n.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(5,2,90)
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.7
    l.new(tc.outputs['Generated'],stretch.inputs[0]);l.new(stretch.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=dark;ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=light
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
cloth=mat('Sofa woven oatmeal',(.48,.45,.38),.95,texture=180)
rugmat=mat('Ivory wool rug',(.62,.60,.54),1,texture=220)
black=mat('Soft black',(.012,.014,.016),.6)
rubber=mat('Driver rubber surrounds',(.009,.010,.011),.75)
cone=mat('Coated paper cone',(.045,.049,.052),.8,texture=150)
mountmat=mat('Graphite printed polymer',(.055,.07,.08),.5,texture=240)
armmat=mat('Terracotta printed swivel arm',(.32,.10,.038),.5,texture=240)
steel=mat('Brushed steel fasteners',(.35,.38,.4),.3,.8)
white=mat('Warm ceramic',(.78,.75,.68),.35)
green=mat('Olive leaves',(.075,.115,.035),.7)
cushionmat=mat('Muted rust cushion',(.32,.11,.055),.95,texture=160)

def box(name,loc,size,material,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:o.data.materials.append(material)
    if bevel:
        b=o.modifiers.new('Soft manufactured edges','BEVEL');b.width=bevel;b.segments=4
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o

def cyl(name,loc,radius,depth,material,axis=(0,0,1),r2=None):
    if r2 is None:bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius,depth=depth,location=loc)
    else:bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=radius,radius2=r2,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(axis))
    o.data.materials.append(material)
    b=o.modifiers.new('Edge highlight','BEVEL');b.width=min(.002,depth/5);b.segments=3
    for f in o.data.polygons:f.use_smooth=True
    o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def sphere(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    return o

def curve(name,points,radius,material):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=3
    s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for b,p in zip(s.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.data.materials.append(material);return o

def transform(o,m):
    bpy.context.view_layer.update();o.matrix_world=m@o.matrix_world

def speaker(name,base):
    # Front faces local +Y; all body geometry fits the designed cabinet envelope.
    created=[]
    def b(*a,**k):o=box(*a,**k);created.append(o);return o
    def c(*a,**k):o=cyl(*a,**k);created.append(o);return o
    b(name+' walnut cabinet',(0,.222,.102),(.150,.150,.180),walnut,.006)
    b(name+' inset front baffle',(0,.297,.102),(.138,.003,.168),black,.004)
    for z,r in [(.075,.049),(.15,.020)]:
        c(name+' driver frame',(0,.300,z),r,.004,black,(0,1,0))
        # Rubber torus surrounds a recessed paper cone.
        bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=16,location=(0,.303,z),major_radius=r*.81,minor_radius=r*.11,rotation=(math.pi/2,0,0))
        o=bpy.context.object;o.name=name+' rolled surround';o.data.materials.append(rubber);created.append(o)
        c(name+' diaphragm',(0,.301,z),r*.71,.004,cone,(0,1,0),r2=r*.42)
        o=sphere(name+' dust cap',(0,.304,z),(r*.32,.007,r*.32),black);created.append(o)
    for x in [-.058,.058]:
        for z in [.032,.172]:c(name+' baffle screw',(x,.300,z),.0015,.001,steel,(0,1,0))
    b(name+' rear terminal plate',(0,.146,.082),(.040,.002,.060),black,.002)
    for x,ma in [(-.009,cushionmat),(.009,black)]:c(name+' terminal',(x,.142,.075),.003,.008,ma,(0,1,0))
    for o in created:transform(o,base)

mount_locations=[]
def mounted(name,wall,rotation,pan):
    base=Matrix.Translation(wall)@Matrix.Rotation(rotation,4,'Z')
    yaw=Matrix.Translation((0,.055,.024))@Matrix.Rotation(math.radians(pan),4,'Z')@Matrix.Translation((0,-.055,-.024))
    tilt=Matrix.Translation((0,.110,.024))@Matrix.Rotation(math.radians(-10),4,'X')@Matrix.Translation((0,-.110,-.024))
    for n,data,m in original:
        o=bpy.data.objects.new(name+' / '+n,data.copy());scene.collection.objects.link(o)
        moving=not (n.startswith('Part_1') or n.startswith('Yaw_'))
        cradle=n.startswith(('Part_3','M4_','Swivel_'))
        pose=yaw@tilt if cradle else yaw if moving else Matrix.Identity(4)
        o.matrix_world=base@pose@Matrix.Diagonal((.001,.001,.001,1))@m
        o.data.materials.clear();o.data.materials.append(armmat if n.startswith('Part_2') else mountmat if n.startswith('Part_') else steel)
        for p in o.data.polygons:p.material_index=0
    speaker(name,base@yaw@tilt)
    for x in [-.03,.03]:
        for z in [-.016,.094]:
            o=cyl(name+' wall screw',(x,.008,z),.004,.002,steel,(0,1,0));transform(o,base)
    points=[base@yaw@tilt@Vector((.009,.14,.075)),base@Vector((.02,.10,-.03)),base@Vector((.012,.018,-.14)),base@Vector((.012,.018,-wall[2]+.09))]
    curve(name+' cable service loop',points,.002,black)
    o=box(name+' slim wall cable cover',(.012,.009,(-wall[2]+.09-.14)/2),(.017,.010,wall[2]-.23),plaster,.003);transform(o,base)
    mount_locations.append(dict(name=name,wall_position_m=wall,pan_deg=pan,tilt_deg=-10))

# Room: front at Y=0, seating faces the TV, surrounds on side walls behind seating.
box('Floor foundation',(0,2.7,-.085),(4.8,5.6,.16),oak)
for row in range(25):
    x=-2.3+row*.19
    for j in range(5):
        start=-.05+j*1.2-(.6 if row%2 else 0)
        lo=max(0,start);hi=min(5.5,start+1.196)
        if hi>lo:box('Oak floorboard',(x,(lo+hi)/2,.002),(.186,hi-lo,.018),oak,.001)
box('Ceiling',(0,4.0,2.86),(4.8,8.2,.12),plaster)
box('Front plaster wall',(0,-.09,1.4),(4.8,.18,2.8),plaster)
box('Left plaster wall',(-2.4,2.7,1.4),(.18,5.6,2.8),plaster)
box('Right plaster wall',(2.4,2.7,1.4),(.18,5.6,2.8),plaster)
for x in [-2.3,2.3]:box('Oak skirting',(x,2.7,.055),(.022,5.4,.09),oak,.003)
box('Front skirting',(0,.015,.055),(4.6,.025,.09),oak,.003)
box('Wool area rug',(0,2.55,.025),(3.35,2.5,.018),rugmat,.04)
# TV and credenza.
box('Floating oak media cabinet',(0,.30,.37),(2.35,.43,.39),oak,.016)
for x in [-.79,0,.79]:
    box('Cabinet front',(x,.522,.37),(.77,.018,.34),oak,.006)
    box('Recessed pull',(x,.537,.48),(.18,.008,.009),black,.003)
box('Television slim housing',(0,.074,1.39),(1.72,.06,.985),black,.015)
screen=mat('Television ambient landscape',(.12,.17,.2),.25)
n=screen.node_tree.nodes;l=screen.node_tree.links;p=n.get('Principled BSDF')
tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Generated'],sep.inputs[0])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for i,(pos,col) in enumerate([(0,(.028,.055,.07,1)),(.28,(.07,.14,.16,1)),(.43,(.22,.29,.29,1)),(.62,(.55,.43,.30,1)),(1,(.18,.29,.37,1))]):
    e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos);e.position=pos;e.color=col
l.new(sep.outputs['Z'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color']);l.new(ramp.outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.35
box('TV image',(0,.109,1.39),(1.677,.003,.941),screen,.003)
# A quiet landscape in the TV's art mode, modelled directly in Blender.
for index,(heights,col) in enumerate([
    ([.42,.52,.58,.48,.70,.53,.57,.41,.46],(.19,.28,.30)),
    ([.24,.32,.26,.40,.35,.43,.25,.34,.27],(.075,.16,.19)),
    ([.12,.17,.23,.16,.20,.12,.22,.15,.18],(.028,.075,.10))]):
    material=mat('TV mountain layer '+str(index),col,.9)
    material.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(*col,1)
    material.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.25
    y=.112+index*.001
    verts=[(-.833,y,.924),(.833,y,.924)]+[(.833-i*1.666/8,y,.924+h) for i,h in enumerate(reversed(heights))]
    mesh=bpy.data.meshes.new('Landscape silhouette');mesh.from_pydata(verts,[],[list(range(len(verts)))]);mesh.materials.append(material)
    o=bpy.data.objects.new('TV landscape ridge',mesh);scene.collection.objects.link(o)
sun=mat('TV pale sun',(.7,.58,.38),.7)
cyl('TV landscape sun',(.42,.114,1.65),.058,.001,sun,(0,1,0))
# Front L/R and centre complete the visual 5.1 arrangement.
for x in [-1.45,1.45]:
    box('Front speaker stand base',(x,.40,.025),(.28,.27,.03),black,.015)
    cyl('Front speaker stand',(x,.40,.44),.019,.83,black)
    box('Stand top plate',(x,.4,.86),(.16,.16,.012),black,.006)
    speaker('Front speaker',Matrix.Translation((x,.178,.862)))
box('Centre speaker',(0,.36,.64),(.46,.18,.14),black,.012)
for x in [-.145,.145]:cyl('Centre driver',(x,.453,.64),.047,.005,cone,(0,1,0))
box('Subwoofer',(-1.9,.42,.25),(.32,.35,.46),black,.018)
cyl('Subwoofer cone',(-1.9,.602,.25),.105,.009,cone,(0,1,0))
# Sofa, its back behind the listener, with individual cushions and feet.
for x in [-1.05,1.05]:
    for y in [2.63,3.35]:cyl('Sofa oak foot',(x,y,.12),.035,.2,oak)
box('Sofa upholstered base',(0,3.02,.32),(2.45,.96,.30),cloth,.095)
box('Sofa back',(0,3.45,.71),(2.42,.23,.72),cloth,.10)
for x in [-1.14,1.14]:box('Sofa arm',(x,3.0,.60),(.25,1.00,.56),cloth,.09)
for x in [-.69,0,.69]:
    box('Seat cushion',(x,2.96,.53),(.68,.76,.19),cloth,.07)
    o=box('Back cushion',(x,3.30,.79),(.68,.23,.52),cloth,.085);o.rotation_euler.x=math.radians(-9)
for x in [-.88,.85]:
    o=box('Rust throw pillow',(x,3.04,.83),(.36,.17,.36),cushionmat,.075);o.rotation_euler=(.12,.18 if x<0 else -.2,.18)
# Coffee table, book and ceramic cup.
cyl('Coffee table top',(-.12,1.94,.40),.53,.05,oak)
for x,y in [(-.40,1.73),(.15,1.73),(-.12,2.2)]:cyl('Coffee table leg',(x,y,.21),.025,.37,oak)
box('Art book',(-.19,1.95,.437),(.28,.21,.025),plaster,.004)
cyl('Ceramic cup',(.13,1.95,.469),.034,.072,white)
cyl('Coffee',(.13,1.95,.506),.028,.001,black)
# Side table and floor lamp.
cyl('Side table top',(-1.65,3.0,.49),.22,.035,walnut)
cyl('Side table stem',(-1.65,3.0,.26),.03,.45,black)
cyl('Side table base',(-1.65,3.0,.035),.16,.025,black)
cyl('Lamp base',(-1.95,3.35,.04),.18,.05,black)
cyl('Lamp stem',(-1.95,3.35,.84),.012,1.6,black)
cyl('Linen lamp shade',(-1.95,3.35,1.64),.21,.32,rugmat,r2=.15)
# Large window panel on left side, with a mullion and sheer-like lit surface.
window=mat('Soft daylight window',(.8,.87,.92),.3)
wp=window.node_tree.nodes.get('Principled BSDF');wp.inputs['Emission Color'].default_value=(.8,.87,.92,1);wp.inputs['Emission Strength'].default_value=1.5
box('Window daylight',(-2.302,1.8,1.65),(.01,1.65,1.6),window)
for y in [.94,1.8,2.66]:box('Window vertical frame',(-2.28,y,1.65),(.055,.035,1.67),oak,.004)
for z in [.83,2.47]:box('Window horizontal frame',(-2.28,1.8,z),(.055,1.76,.04),oak,.004)
# Plant near screen.
cyl('Plant ceramic pot',(1.96,.76,.24),.16,.44,white,r2=.20)
import random
random.seed(9)
for i in range(15):
    a=i*2.4;h=random.uniform(.75,1.48);tip=(1.96+math.cos(a)*.26,.76+math.sin(a)*.23,h)
    curve('Plant branch',[(1.96,.76,.40),(1.96,.76,h*.8),tip],.006,walnut)
    o=sphere('Plant leaf',tip,(.055,.007,.13),green);o.rotation_euler=(.35,random.uniform(-.8,.8),a)
mounted('Surround left',(-2.31,3.95,1.55),-math.pi/2,-28)
mounted('Surround right',(2.31,3.95,1.55),math.pi/2,28)

def area(name,loc,target,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Large soft window key',(-2.1,1.8,2.1),(0,2.6,.5),500,(.84,.91,1),2)
area('Open ceiling daylight',(0,2.5,4),(0,2.5,0),350,(1,.90,.76),4)
area('Rear soft fill',(0,5.1,2.6),(0,3,1),140,(1,.88,.73),2.5)
area('Lamp warm glow',(-1.95,3.35,1.52),(-1.9,3.35,.5),12,(1,.66,.33),.25)
scene.world=bpy.data.worlds.new('Daylight environment');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.55,.7,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.18
scene.render.engine='CYCLES';scene.cycles.samples=24 if PREVIEW else 160
scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    scene.cycles.device='GPU'
except Exception as e:print('GPU fallback',e)
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.film_transparent=False

def camera(name,loc,target,lens):
    bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=name;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;o.data.clip_start=.01;o.data.clip_end=100;return o
wide=camera('01 — room showcase',(.65,7.50,2.48),(0,2.4,1.23),25)
close=camera('02 — mount in use',(1.53,4.54,1.97),(2.15,3.83,1.64),53)
scene.camera=wide
# Keep both complete wall mounts inside a deliberate frame margin.
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
scene.render.resolution_x=2000;scene.render.resolution_y=1400
for _ in range(30):
    projected=[world_to_camera_view(scene,wide,o.matrix_world@Vector(c)) for o in scene.objects if '/ Part_' in o.name for c in o.bound_box]
    if all(.075 < p.x < .925 and .075 < p.y < .925 for p in projected):break
    wide.data.lens*=.97
print('SHOWCASE_LENS',wide.data.lens)
scene['Description']='Illustrative 5.1 living room; actual revision 3 mount meshes; unbranded speakers matching the CAD cabinet envelope.'
(OUT/'scene_manifest.json').write_text(json.dumps({'units':'metres','speaker_cabinet_mm':[150,150,180],'mount_source':'output_blender/surround_mount.blend','surrounds':mount_locations},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'living_room.blend'))
for cam,name,size in [(wide,'living-room',(2000,1400)),(close,'mount-in-use',(1800,1500))]:
    scene.camera=cam;scene.render.resolution_x=size[0]//2 if PREVIEW else size[0];scene.render.resolution_y=size[1]//2 if PREVIEW else size[1]
    scene.render.filepath=str(OUT/(name+('-preview' if PREVIEW else '')+'.png'))
    bpy.ops.render.render(write_still=True)
scene.camera=wide
scene.render.resolution_x=2000;scene.render.resolution_y=1400
scene.render.filepath=str(OUT/'living-room.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'living_room.blend'))
