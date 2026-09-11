"""Package the final design and room visualization, excluding backups/previews."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json
root=Path(__file__).resolve().parent
packages={
 'eris-rail-mount-design.zip':[root/'README.md',*[root/p for p in ['design.py','validate.py','installation.py','make_documents.py','fabrication.py']],*sorted((root/'cad').glob('*.json')),*sorted((root/'cad').glob('*.pdf')),*sorted((root/'cad').glob('*.step')),*sorted((root/'cad').glob('*.FCStd')),*sorted((root/'print').rglob('*.stl')),*sorted((root/'print').rglob('*.json')),root/'render'/'installation.json',root/'render'/'mount_inspection.blend',root/'render'/'mount-studio.png',root/'render'/'mount-service.png'],
 'dorm-room-render-pack.zip':[root/'README.md',root/'render_room.py',root/'check_scene.py',root/'studio_view.py',*[root/'render'/p for p in ['dorm_room.blend','room.png','mount.png','overview.png','rail-wall.png','mount_meshes.json','room_meshes.json','installation.json','scene_validation.json','mount_inspection.blend','mount-studio.png','mount-service.png']]]
}
for name,files in packages.items():
 with ZipFile(root/name,'w',ZIP_DEFLATED,compresslevel=6) as z:
  for p in files:
   assert p.is_file(),p
   z.write(p,p.relative_to(root))
 with ZipFile(root/name) as z:assert z.testzip() is None
 print(name,(root/name).stat().st_size,'bytes',len(files),'files')
