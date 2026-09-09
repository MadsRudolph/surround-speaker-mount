# Compact speaker mount — print files

Print 2 × each STL for a pair of speakers (six printed parts total).
These are the compact revision 3 FreeCAD exports, already oriented on their X sides.
Import in millimetres and do not auto-scale.

| File | Quantity for pair | Bounding box X × Y × Z |
|---|---:|---|
| Part_1_WallPlate.stl | 2 | 140 × 77 × 90 mm |
| Part_2_SwivelArm.stl | 2 | 44 × 99 × 48.6 mm |
| Part_3_Cradle.stl | 2 | 68.4 × 215 × 186 mm |

PETG or ASA; 0.4 mm nozzle; 0.20 mm layers; 6 walls; 6–8 top/bottom layers;
45–50% gyroid. Use local solid infill around joints and insert bosses.
Supports are required beneath ears, raised rails and horizontal bores; inspect the
slicer preview and enable internal supports where needed. Use a brim. A 250 mm
bed is recommended; a 220 mm bed has only 5 mm spare along the cradle length.
Check your slicer's estimated print duration before planning an overnight batch.

Read the root README for the M5 joint hardware, M4 inserts, pressure feet, foam,
wall fixings and assembly. The insert bore is 5.6 mm: confirm it matches your inserts.
The terminal panel is assumed 40 mm wide, 60 mm tall, starting 40 mm above the
cabinet bottom, with 30 mm rear plug projection; panel height/projection are unconfirmed.
This is a prototype without a load rating; inspect and load-test before wall use.

## Indexed tilt interface

The up/down pivot now seats in **5° steps** using a 72-tooth mating ring. Pan stays
smooth and continuously adjustable. Reprint both arm and cradle; the wall plate
is unchanged. Do not mix smooth revision 2 and toothed revision 3 mating parts.

Print `fit-coupons/Tilt_Female_Coupon.stl` and `fit-coupons/Tilt_Male_Coupon.stl`
first, with toothed faces up. Inspect the slicer for preserved teeth. Use
0.10–0.12 mm layers through the teeth and check fit without forcing. The minimum
nominal crest width is about 0.42 mm, so a 0.4 mm nozzle is at the fine-feature
limit. Adjust the process or use a smaller nozzle if details are lost.

The arm print orientation is flipped from revision 2 to point its toothed face
up. Keep support contact off the teeth and route supports for the opposing ear
from smooth areas or the bed. The cradle also has its toothed face pointing up.

Support the speaker, loosen the tilt bolt, slide the cradle toward the smooth
cheek to clear the teeth, choose a 5° position, seat and retighten. Do not ratchet
the teeth under load. Nominal release travel from seated is 0.6 mm. Printed fit,
tooth strength and holding performance remain unverified.
