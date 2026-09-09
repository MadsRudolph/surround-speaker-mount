"""Run in background Blender; turns the existing visualization into a posing rig."""
import bpy,math,json
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output_blender/surround_mount.blend'))
scene=bpy.context.scene
yaw=bpy.data.objects['Pan_Z_minus60_plus60']
pitch=bpy.data.objects['Tilt_X_minus30_zero']
for obj in (yaw,pitch):
    obj.animation_data_clear()
    obj.rotation_euler=(0,0,0)
control=bpy.data.objects.new('AIM_CONTROLS',None)
scene.collection.objects.link(control)
control.location=(0,55,24)
control.empty_display_type='CIRCLE'
control.empty_display_size=35
control.show_in_front=True
control['Pan_degrees']=0.0
control['Tilt_degrees']=0.0
control.id_properties_ui('Pan_degrees').update(min=-60,max=60,soft_min=-60,soft_max=60,description='Swivel about the vertical wall pivot')
control.id_properties_ui('Tilt_degrees').update(min=-30,max=0,soft_min=-30,soft_max=0,description='Tilt down about the cradle pivot')
for obj,index,key in [(yaw,2,'Pan_degrees'),(pitch,0,'Tilt_degrees')]:
    curve=obj.driver_add('rotation_euler',index)
    d=curve.driver;d.type='SCRIPTED'
    v=d.variables.new();v.name='angle';v.type='SINGLE_PROP'
    v.targets[0].id=control;v.targets[0].data_path='["'+key+'"]'
    d.expression=('round(angle / 5) * 5' if key=='Tilt_degrees' else 'angle') + ' * 0.017453292519943295'
# Keep geometry selectable for inspecting, but protect accidental object transforms.
for obj in scene.objects:
    if obj.type=='MESH':
        obj.lock_location=(True,True,True)
        obj.lock_rotation=(True,True,True)
        obj.lock_scale=(True,True,True)
# Check nested transforms at several poses. Get evaluated driver/constraint results.
for pan,tilt in [(0,0),(60,-30),(-60,-30),(25,-12)]:
    control['Pan_degrees']=pan;control['Tilt_degrees']=tilt
    control.update_tag();bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    expected=Matrix.Translation((0,55,24)) @ Matrix.Rotation(math.radians(pan),4,'Z') @ Matrix.Translation((0,55,0)) @ Matrix.Rotation(math.radians(round(tilt/5)*5),4,'X')
    actual=pitch.evaluated_get(deps).matrix_world
    assert max(abs(actual[i][j]-expected[i][j]) for i in range(4) for j in range(4))<1e-4
control['Pan_degrees']=0.;control['Tilt_degrees']=0.
control.update_tag();bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
control.select_set(True);bpy.context.view_layer.objects.active=control
# Open Object Properties and an assembly view, with the control preselected.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='PROPERTIES':area.spaces.active.context='OBJECT'
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.clip_end=5000
            space.region_3d.view_distance=480
            space.region_3d.view_location=(0,150,65)
            space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
            space.shading.color_type='MATERIAL'
            space.show_region_ui=True
readme=bpy.data.texts.new('START_HERE — how to aim')
readme.write('Select AIM_CONTROLS. In Object Properties > Custom Properties, drag Pan_degrees and Tilt_degrees.\nPan: -60 to +60 degrees. Tilt: -30 to 0 degrees, snapped to 5-degree steps. Set both to zero to reset.\nNo animation keyframes override your edits. Native drivers and constraints do not require an addon.\n')
path=ROOT/'output_blender/interactive_assembly.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('BLENDER_INTERACTIVE_VERIFIED',path)
