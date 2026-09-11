"""Run in Blender to verify saved aiming controls without altering the scene file."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'render'/'dorm_room.blend'))
install=json.loads((ROOT/'render'/'installation.json').read_text())
results=[]
def changed(a,b):return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))>1e-5
for p in install['placements']:
    prefix=p['name']+' / '
    control=bpy.data.objects[prefix+'AIM CONTROLS']
    shoe=bpy.data.objects[prefix+'Rail_Shoe'];yoke=bpy.data.objects[prefix+'Pan_Yoke'];cradle=bpy.data.objects[prefix+'Eris_Cradle']
    speaker=bpy.data.objects[prefix+'Eris cabinet']
    bpy.context.view_layer.update()
    actual=speaker.matrix_world@Vector((0,.081,.066));expected=Vector(p['tweeter_world_mm'])/1000
    error=(actual-expected).length
    assert error<1e-5,(prefix,error,list(actual),list(expected))
    before=[o.matrix_world.copy() for o in [shoe,yoke,cradle]]
    original_pan=control['pan_deg'];control['pan_deg']=original_pan-5 if original_pan>0 else original_pan+5
    control.update_tag();bpy.context.scene.frame_set(2);bpy.context.view_layer.update()
    assert not changed(before[0],shoe.matrix_world)
    assert changed(before[1],yoke.matrix_world) and changed(before[2],cradle.matrix_world)
    before=[o.matrix_world.copy() for o in [shoe,yoke,cradle]]
    control['tilt_step']=10;control.update_tag();bpy.context.scene.frame_set(3);bpy.context.view_layer.update()
    assert not changed(before[0],shoe.matrix_world) and not changed(before[1],yoke.matrix_world)
    assert changed(before[2],cradle.matrix_world)
    results.append({'mount':p['name'],'initial_tweeter_error_m':error,'pan_moves_yoke_and_cradle':True,'tilt_moves_only_cradle':True,'shoe_remains_fixed':True})
(ROOT/'render'/'scene_validation.json').write_text(json.dumps(results,indent=2))
print('SCENE CONTROLS VERIFIED',json.dumps(results),flush=True)
