# Living-room product showcase

An illustrative 5.1 surround setup with the revision 3 mount on both side walls,
behind the sofa. The room, furniture, speaker cabinets, drivers, materials and
lighting are modelled in Blender. No external models or image assets are needed.

- `living_room.blend`: editable scene, with room and product-detail cameras.
- `living-room.png`: room-wide render.
- `mount-in-use.png`: installed-mount detail.
- `render_living_room.py`: reproducible scene builder and Cycles renderer.
- `scene_manifest.json`: source geometry, cabinet size and mount poses.

Run from the repository root:

```sh
blender -b --python showcase/render_living_room.py
```

Add `-- --preview` for half-resolution previews. CUDA is used when available.
The builder reads `output_blender/surround_mount.blend` and copies the original
mount meshes, scaling millimetres to metres and applying pan/tilt transforms.
It does not change manufacturing geometry or exports.

Speakers are unbranded visual models matching the 150 × 150 × 180 mm cabinet
envelope, not a representation of a verified commercial speaker. Each surround
uses 28° inward pan and 10° downward tilt. Room layout and cables are illustrative;
these renders do not establish load capacity, installation safety or acoustic
performance. Physical fit and load testing remain pending.

## Animated pan and tilt

`mount-motion.gif` is a six-second, 96-frame loop at 720 × 600 pixels.
`mount_animation.blend` contains the animated joints and fixed product camera.
The wall plate stays fixed; the swivel arm turns about the yaw pivot, and the
cradle and speaker tilt together about the pitch pivot. The cable endpoint follows
the speaker while the wall cable cover stays fixed.

```sh
blender -b --python showcase/animate_mount.py
ffmpeg -y -framerate 16 -i showcase/animation-frames/%04d.png -filter_complex "[0:v]split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" -loop 0 showcase/mount-motion.gif
```

Yaw follows ±60° continuously. Tilt disengages axially, advances in 5° steps from 0° to −30°, and re-seats at each step. Frame 97 is the same pose as
frame 1 and is excluded from the GIF to avoid a repeated endpoint. The animation
is a kinematic illustration, not a demonstration of tested load performance.

`tilt-teeth.png` shows the two optional fit coupons carrying the exact arm and
cradle tooth profiles. Recreate it with `blender -b --python showcase/render_tilt_detail.py`;
`tilt_detail.blend` is the editable scene.
