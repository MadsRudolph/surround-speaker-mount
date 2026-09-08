from pathlib import Path
import sys,json
sys.path.insert(0,'/usr/lib/freecad/lib')
import FreeCAD as App
import FreeCADGui as Gui
Gui.showMainWindow()
root=Path(__file__).resolve().parent
path=root/'output_freecad/interactive_assembly.FCStd'
doc=App.openDocument(str(path))
names=['PanJoint','TiltJoint','Part_1_WallPlate','Part_1_WallPlate_Solid','Part_2_SwivelArm','Part_2_SwivelArm_Solid','Part_3_Cradle','Part_3_Cradle_Solid','SpeakerEnvelope','TerminalPanel']
print('BEFORE',[(n,doc.getObject(n).ViewObject.Visibility) for n in names],flush=True)
for n in names:doc.getObject(n).ViewObject.Visibility=True
colors={'Part_1_WallPlate':(.22,.32,.40),'Part_2_SwivelArm':(.75,.36,.12),'Part_3_Cradle':(.23,.45,.49),'SpeakerEnvelope':(.10,.11,.12),'TerminalPanel':(.02,.02,.02)}
for n,color in colors.items():
    obj=doc.getObject(n)
    obj.ViewObject.ShapeColor=color
    if hasattr(obj,'Tip') and obj.Tip:obj.Tip.ViewObject.ShapeColor=color
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
doc.recompute()
out=root/'output_freecad/interactive_assembly_visible.FCStd'
doc.saveAs(str(out))
App.closeDocument(doc.Name)
doc=App.openDocument(str(out))
print('AFTER_REOPEN',[(n,doc.getObject(n).ViewObject.Visibility) for n in names],flush=True)
assert all(doc.getObject(n).ViewObject.Visibility for n in names)
App.closeDocument(doc.Name)
print('VISIBILITY_REPAIR_VERIFIED',str(out),flush=True)
Gui.getMainWindow().close()
