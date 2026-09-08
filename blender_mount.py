"""Standalone: blender --background --python blender_mount.py
Creates a dedicated scene; preserves other scenes. Numeric mesh units are mm.
STLs are in mm, separately oriented on X sides for printing.
"""
import bpy, bmesh, math, json, struct
from pathlib import Path
from mathutils import Vector, Matrix
# Units: millimetres. X right, Y away from wall, Z up.
DEFAULTS = dict(Speaker_Width=150., Speaker_Depth=150., Speaker_Height=180.,
    Clamp_Padding_Offset=2., Insert_Hole_Diameter=5.6, Wall_Thickness=4.)
NAMES = ['Part_1_WallPlate', 'Part_2_SwivelArm', 'Part_3_Cradle']
YAW = (0.,55.,24.)
PITCH = (0.,110.,24.)

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
    return parts

OUT=Path(__file__).resolve().parent/'output_blender'
OUT.mkdir(exist_ok=True)
scene=bpy.data.scenes.new('Surround Speaker Mount')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=.001
scene.unit_settings.length_unit='MILLIMETERS'

def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj

def apply(obj,mod):
    activate(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

def primitive(s):
    if s[0]=='box':
        _,a,b,r=s
        bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)])
        obj=bpy.context.object
        obj.dimensions=[b[i]-a[i] for i in range(3)]
    elif s[0]=='cone':
        _,a,r1,r2,length,axis=s
        direction=Vector({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis])
        bpy.ops.mesh.primitive_cone_add(vertices=96,radius1=r1,radius2=r2,depth=length,location=Vector(a)+direction*length/2)
        obj=bpy.context.object
        obj.rotation_mode='QUATERNION'
        obj.rotation_quaternion=Vector((0,0,1)).rotation_difference(direction)
        r=0
    else:
        _,a,radius,length,axis,r=s
        direction=Vector({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis])
        bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=radius,depth=length,
            location=Vector(a)+direction*length/2)
        obj=bpy.context.object
        obj.rotation_mode='QUATERNION'
        obj.rotation_quaternion=Vector((0,0,1)).rotation_difference(direction)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if r:
        mod=obj.modifiers.new('Rounded edges','BEVEL')
        mod.width=r
        mod.segments=4
        apply(obj,mod)
    return obj

def boolean(obj,tool,operation):
    mod=obj.modifiers.new(operation,'BOOLEAN')
    mod.operation=operation
    mod.solver='EXACT'
    mod.object=tool
    apply(obj,mod)
    bpy.data.objects.remove(tool,do_unlink=True)

def clean(obj):
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    # Exact booleans can leave one missing planar quad on a cylindrical bore.
    # Repair only a single tiny four-edge boundary; never cap a designed bore.
    boundary=[e for e in bm.edges if e.is_boundary]
    repaired=0
    if len(boundary)==4:
        vs=list({v for e in boundary for v in e.verts})
        span=max(max(v.co[i] for v in vs)-min(v.co[i] for v in vs) for i in range(3))
        if len(vs)==4 and span<3:
            repaired=len(bmesh.ops.holes_fill(bm,edges=boundary,sides=4)['faces'])
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bad=sum(not e.is_manifold for e in bm.edges)
    remaining=set(bm.verts)
    components=0
    while remaining:
        components+=1
        todo=[remaining.pop()]
        while todo:
            for e in todo.pop().link_edges:
                for v in e.verts:
                    if v in remaining:
                        remaining.remove(v)
                        todo.append(v)
    volume=bm.calc_volume(signed=True)
    if volume<0:
        bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        volume=-volume
    bm.to_mesh(obj.data)
    bm.free()
    if bad or components!=1 or volume<=0:
        raise RuntimeError(f'{obj.name}: {bad} nonmanifold edges, {components} components')
    return dict(nonmanifold_edges=bad,components=components,volume_mm3=volume,repaired_small_quads=repaired)

def stl(obj,path):
    # Custom binary writer avoids version-dependent STL operators and unit ambiguity.
    obj.data.calc_loop_triangles()
    rot=Matrix.Rotation(math.pi/2,4,'Y')
    vertices=[rot @ (obj.matrix_world @ v.co) for v in obj.data.vertices]
    mins=Vector([min(v[i] for v in vertices) for i in range(3)])
    vertices=[v-mins for v in vertices]
    with path.open('wb') as f:
        f.write(b'Surround mount | units mm | print X-side'.ljust(80,b' '))
        f.write(struct.pack('<I',len(obj.data.loop_triangles)))
        for tri in obj.data.loop_triangles:
            a,b,c=[vertices[i] for i in tri.vertices]
            n=(b-a).cross(c-a).normalized()
            f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
    return [max(v[i] for v in vertices) for i in range(3)]

def material(name,color):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=.32
    return mat

colors=[(.12,.17,.23),(.65,.28,.08),(.16,.32,.38)]
parts=[]
report={}
for name,(adds,cuts),color in zip(NAMES,geometry(DEFAULTS),colors):
    obj=primitive(adds[0])
    obj.name=name
    for s in adds[1:]: boolean(obj,primitive(s),'UNION')
    for s in cuts: boolean(obj,primitive(s),'DIFFERENCE')
    report[name]=clean(obj)
    report[name]['print_bounds_mm']=stl(obj,OUT/(name+'.stl'))
    obj.data.materials.clear()
    obj.data.materials.append(material(name+'_PETG',color))
    for polygon in obj.data.polygons: polygon.material_index=0
    parts.append(obj)

# Empty origins are the actual pivot centers, not object bounding box centers.
def empty(name,location):
    obj=bpy.data.objects.new(name,None)
    scene.collection.objects.link(obj)
    obj.location=location
    obj.empty_display_size=15
    return obj

def parent_keep(obj,parent):
    bpy.context.view_layer.update()
    world=obj.matrix_world.copy()
    obj.parent=parent
    obj.matrix_world=world

def limit(obj,axis,lo,hi):
    obj.rotation_mode='XYZ'
    c=obj.constraints.new('LIMIT_ROTATION')
    c.owner_space='LOCAL'
    c.use_limit_x=c.use_limit_y=c.use_limit_z=True
    setattr(c,'min_'+axis,math.radians(lo))
    setattr(c,'max_'+axis,math.radians(hi))
    c.use_transform_limit=True

yaw=empty('Pan_Z_minus60_plus60',YAW)
parent_keep(parts[1],yaw)
pitch=empty('Tilt_X_minus30_zero',PITCH)
parent_keep(pitch,yaw)
parent_keep(parts[2],pitch)
limit(yaw,'z',-60,60)
limit(pitch,'x',-30,0)
# Cabinet envelope only, never exported as a printable part.
w,d,h=DEFAULTS['Speaker_Width'],DEFAULTS['Speaker_Depth'],DEFAULTS['Speaker_Height']
pad=DEFAULTS['Clamp_Padding_Offset']
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,145+pad+d/2,10+pad+h/2))
speaker=bpy.context.object
speaker.name='Speaker_envelope_NOT_FOR_PRINT'
speaker.dimensions=(w,d,h)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
speaker.data.materials.append(material('Speaker graphite',(.035,.04,.045)))
parent_keep(speaker,pitch)
for frame,pan,tilt in [(1,0,0),(60,-60,-30),(120,60,-30),(180,0,0)]:
    yaw.rotation_euler.z=math.radians(pan)
    pitch.rotation_euler.x=math.radians(tilt)
    yaw.keyframe_insert(data_path='rotation_euler',frame=frame)
    pitch.keyframe_insert(data_path='rotation_euler',frame=frame)
scene.frame_start=1
scene.frame_end=180
scene.frame_set(1)
# Hardware envelopes for illustration, excluded from all STL exports.
steel=material('Steel hardware',(.35,.38,.42))
def hardware(name,s,parent=None):
    obj=primitive(s)
    obj.name=name+'_NOT_FOR_PRINT'
    obj.data.materials.clear()
    obj.data.materials.append(steel)
    for polygon in obj.data.polygons: polygon.material_index=0
    if parent: parent_keep(obj,parent)
    return obj
hardware('Yaw_M5x60',('cyl',(0,55,-1.5),2.5,60,'Z',0))
hardware('Yaw_head',('cyl',(0,55,-6.5),4.25,5,'Z',.3))
for z in (-1.5,48): hardware('Yaw_washer',('cyl',(0,55,z),7.5,1.5,'Z',.1))
hardware('Yaw_locknut_envelope',('cyl',(0,55,49.5),4.6,5,'Z',.1))
hardware('Pitch_M5x60',('cyl',(-25.8,110,24),2.5,60,'X',0),yaw)
hardware('Pitch_head',('cyl',(-30.8,110,24),4.25,5,'X',.3),yaw)
for x in (-25.8,24.3): hardware('Pitch_washer',('cyl',(x,110,24),7.5,1.5,'X',.1),yaw)
hardware('Pitch_locknut_envelope',('cyl',(25.8,110,24),4.6,5,'X',.1),yaw)
inner=w/2+pad+4
for sign in (-1,1):
    for y in (145+d*.3,145+d*.75):
        x=(-inner-14 if sign<0 else inner-4)
        hardware('M4_clamp_screw',('cyl',(x,y,h*.27),2,18,'X',0),pitch)
        x=(-inner if sign<0 else inner-4)
        foot=hardware('Swivel_foot_envelope',('cyl',(x,y,h*.27),8,4,'X',.3),pitch)
# Measured panel width/lower edge; height is a provisional 60 mm envelope.
panel=primitive(('box',(-20,146.5,52),(20,147.1,112),.1))
panel.name='Terminal_panel_40x60_HEIGHT_ASSUMED'
panel.data.materials.clear()
panel.data.materials.append(material('Black terminal panel',(.005,.005,.005)))
parent_keep(panel,pitch)
# Studio overview.
bpy.ops.object.camera_add(location=(480,640,420))
camera=bpy.context.object
camera.name='Assembly_camera'
camera.rotation_euler=(Vector((0,175,90))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'
camera.data.ortho_scale=490
camera.data.clip_end=5000
scene.camera=camera
for loc,power,size in [((200,200,600),18000000,350),((-350,100,250),12000000,300)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    light=bpy.context.object
    light.data.energy=power
    light.data.shape='DISK'
    light.data.size=size
    light.rotation_euler=(Vector((0,150,70))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Studio')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.15,.15,1)
scene.render.engine='CYCLES'
scene.cycles.samples=32
scene.render.resolution_x=1200
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'assembly.png')
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'surround_mount.blend'))
bpy.ops.render.render(write_still=True)
speaker.hide_render=True
panel.hide_render=True
scene.render.filepath=str(OUT/'assembly_without_speaker.png')
bpy.ops.render.render(write_still=True)
speaker.hide_render=False
panel.hide_render=False
# Rear terminal view: hide fixed plate for visibility only, not for collision checks.
old_camera_matrix=camera.matrix_world.copy()
old_scale=camera.data.ortho_scale
parts[0].hide_render=True
camera.location=(250,-170,170)
camera.rotation_euler=(Vector((0,155,90))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=280
scene.render.filepath=str(OUT/'terminal_clearance.png')
bpy.ops.render.render(write_still=True)
parts[0].hide_render=False
camera.matrix_world=old_camera_matrix
camera.data.ortho_scale=old_scale

print('MOUNT_VALIDATED',json.dumps(report))
