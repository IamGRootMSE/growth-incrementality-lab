"""Package an allowlisted source handoff; raw data, environments and secrets excluded."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def package():
    report_dir=ROOT/'outputs/reports'
    for name in ['interview-guide','methodology','provenance']:
        shutil.copy2(ROOT/'docs'/f'{name}.md',report_dir/f'{name}.md')
    shutil.copy2(ROOT/'README.md',report_dir/'project-readme.md')
    files=[]
    for name in ['.gitignore','LICENSE','README.md','requirements.txt','requirements.lock','requirements-browser.txt','requirements-pdf.txt','pytest.ini']:
        files.append(ROOT/name)
    for name in ['lab','sql','site','scripts','tests','docs','.github','outputs/analysis','outputs/reports','outputs/screenshots','outputs/site']:
        files.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='overflow-debug.png')
    manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    zip_path=ROOT/'outputs/growth-incrementality-lab.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):z.write(p,p.relative_to(ROOT))
        z.writestr('PACKAGE-MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        assert not any(n.startswith(('data/','work/','.git/')) or '.env' in n for n in z.namelist())
    print(json.dumps({'archive':str(zip_path),'files':len(files),'bytes':zip_path.stat().st_size,'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':package()
