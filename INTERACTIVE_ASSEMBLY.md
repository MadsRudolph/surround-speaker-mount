# Move the mount interactively

## Blender

Open `output_blender/interactive_assembly.blend`.

1. `AIM_CONTROLS` is preselected. Select it in the Outliner if needed.
2. In the **Object Properties** tab (orange square icon), expand **Custom Properties**.
3. Drag or type **Pan_degrees** (−60…60) and **Tilt_degrees** (−30…0).
4. Set both to zero to return to level and straight.

The wall stays fixed; the arm swivels around the vertical pin; the cradle, cabinet, terminal panel and clamp hardware tilt around the horizontal pin and follow pan. The controls use native Blender drivers and rotation constraints. No add-on or Python auto-run permission is required. Demonstration animation was removed so moving the timeline cannot reset your pose. Mesh transforms are locked against accidental movement; adjust the two controls instead.

## FreeCAD

Open `output_freecad/interactive_assembly_visible.FCStd` (the standard `interactive_assembly.FCStd` has also been corrected). Close the earlier copy first, then open this file and press **V, F** to fit the whole assembly.

1. Select **AIM CONTROLS — edit Pan / Tilt below** in the model tree.
2. In the **Data** property tab, expand **Aiming**.
3. Change **Pan** (−60…60) and **Tilt** (−30…0); press Enter to apply.
4. Set both to zero to reset. If automatic recompute is disabled, press F5.

For live mouse dragging, sliders and part colors, open `Open_Interactive_Assembly.FCMacro` through **Macro → Macros → select the file → Execute**. The macro opens the assembly and adds a **Speaker — Pan & Tilt** dock with a drag pad, sliders and a reset button. Hold the left mouse button in the pad: drag left/right for pan and up/down for tilt. The model updates continuously. Keep the macro beside the output folders. The native property controls work without running it.

The FreeCAD assembly uses nested `App::Part` groups and native placement expressions, not Assembly-workbench solver joints. No additional workbench or custom Python proxy is needed. It includes the cabinet and provisional terminal panel. Its printed-part shapes are snapshots of the compact design, so posing is quick and does not rebuild the geometry. To update geometry, regenerate the parametric source and rerun `make_interactive_freecad.py`.

Both files open at zero pan/tilt and can save your chosen pose. These are kinematic previews, not simulations of flex, friction or load capacity. The original manufacturing models and STL print orientations remain in their existing files.

Validation: native FreeCAD placements and evaluated Blender driver transforms were compared against independent rotation matrices at (pan, tilt) = (0,0), (60,−30), (−60,−30), and (25,−12). The FreeCAD file was also reopened and checked at (45,−20). The FreeCAD drag pad was exercised in a live GUI session: simulated press/move/release events updated pan and tilt, then restored the starting pose. Results are saved in `live_drag_validation.json`.
