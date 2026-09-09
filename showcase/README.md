# Living-room product showcase

An illustrative 5.1 surround setup with the revision 2 mount on both side walls,
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
uses 28° inward pan and 12° downward tilt. Room layout and cables are illustrative;
these renders do not establish load capacity, installation safety or acoustic
performance. Physical fit and load testing remain pending.
