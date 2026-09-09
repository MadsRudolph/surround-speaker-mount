"""Render face-up fit coupons using the exact manufactured tooth profiles."""
import bpy,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.unit_settings.system='METRIC'
def material(name,color,rough=.4):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m
female=material('Terracotta arm material',(.32,.10,.038))
male=material('Graphite cradle material',(.055,.07,.08))
back=material('Warm studio paper',(.55,.52,.46),.9)
textmat=material('Dark caption ink',(.025,.032,.035),.8)
for name,x,mat in [('Tilt_Female_Coupon',-.027,female),('Tilt_Male_Coupon',.027,male)]:
 bpy.ops.wm.stl_import(filepath=str(OUT.parent/'print/fit-coupons'/(name+'.stl')))
 o=bpy.context.object;o.name=name;o.scale=(.001,)*3;o.location=(x-.022,-.022,0);o.data.materials.append(mat)
bpy.ops.mesh.primitive_plane_add(size=2)
bpy.context.object.data.materials.append(back)
bpy.context.object.location.z=-.0002
for text,x in [('RECESSED ARM FACE',-.027),('RAISED CRADLE FACE',.027)]:
 bpy.ops.object.text_add(location=(x,-.031,.0001))
 o=bpy.context.object;o.data.body=text;o.data.align_x='CENTER';o.data.size=.0026;o.data.materials.append(textmat)
for loc,power,size in [((-.06,-.02,.065),.2,.025),((.04,.06,.1),.15,.06)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.017,-.105,.125));c=bpy.context.object;c.rotation_euler=(Vector((0,-.001,0))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=.115;c.data.clip_start=.001;s.camera=c
s.world=bpy.data.worlds.new('Studio world');s.world.color=(.25,.25,.25)
s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
s.cycles.device='GPU'
s.view_settings.view_transform='AgX'
s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.filepath=str(OUT/'tilt-teeth.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'tilt_detail.blend'))
bpy.ops.render.render(write_still=True)
