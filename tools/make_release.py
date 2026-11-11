"""Zips the source version (for Python users, macOS/Linux, or building the .exe): the GUI, launchers, logic and libraries. No game files, caches, seeds or
personal settings are included.

Usage:  python -m tools.make_release      -> output/release/OoT-Remake-Rando-<version>.zip
"""
import os,zipfile
from lib.build import VERSION
from lib.game import PROJECT

FILES=['app.py','config.example.json','build_exe.ps1','build_exe.bat','gui.py','run.bat','run.sh','README_TESTERS.md','README.md','logic_seed.py','verify.py','tweaks_mod.py']
FOLDERS=['lib','logic','web']

def main():
    out=os.path.join(PROJECT,'output','release'); os.makedirs(out,exist_ok=True)
    path=os.path.join(out,'OoT-Remake-Rando-%s.zip'%VERSION); root='OoT-Remake-Rando-%s/'%VERSION; n=0
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            info=zipfile.ZipInfo(root+f); info.external_attr=(0o755 if f.endswith('.sh') else 0o644)<<16
            info.compress_type=zipfile.ZIP_DEFLATED; z.writestr(info,open(os.path.join(PROJECT,f),'rb').read()); n+=1
        for d in FOLDERS:
            for dp,dns,fns in os.walk(os.path.join(PROJECT,d)):
                dns[:]=[x for x in dns if x!='__pycache__']
                for fn in sorted(fns):
                    if fn.endswith('.pyc'): continue
                    full=os.path.join(dp,fn); z.write(full,root+os.path.relpath(full,PROJECT).replace(os.sep,'/')); n+=1
    print('%d files -> %s (%d KB)'%(n,path,os.path.getsize(path)//1024))

if __name__=='__main__': main()
