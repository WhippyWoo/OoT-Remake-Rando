# Access to the game dump: where files are, zstd (de)compression, and the zstd dictionaries.
import os,sys,glob,json
from .sarc import sarc_files
from . import zst

TITLE_ID='0400486024DEC000'
if getattr(sys,'frozen',False):            # packaged .exe (PyInstaller)
    PROJECT=os.path.dirname(sys.executable)      # settings, cache and seeds live next to the .exe
    RESOURCES=getattr(sys,'_MEIPASS',PROJECT)    # bundled read-only files (web/)
else:
    PROJECT=RESOURCES=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BCETT_DICT='bcett.byml.zsdic'
ZS_DICT='zs.zsdic'  # used by most other .zs files (events, GameData)

def config():
    p=os.path.join(PROJECT,'config.json')
    return json.load(open(p)) if os.path.exists(p) else {}

def zread(path,dict_=None):
    return zst.decompress(open(path,'rb').read(),dict_)

def zwrite(data,path,dict_=None):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    open(path,'wb').write(zst.compress(data,dict_))

SUPPORTED_VERSION='1.1.1'   # update files: GameDataList.Product.110, ResourceSizeTable.Product.111

def find_romfs(path):
    """Accepts a romfs folder, a folder containing 'romfs', or a dump folder with base/ and updates/.
    Returns (base_romfs, update_romfs) as far as they can be found."""
    if not path: return None,None
    path=os.path.abspath(os.path.expanduser(path))
    if os.path.isdir(os.path.join(path,'base','romfs')):
        ups=sorted(glob.glob(os.path.join(path,'updates','*','romfs')),key=lambda p:(len(p),p))
        return os.path.join(path,'base','romfs'),(ups[-1] if ups else None)
    if os.path.isdir(os.path.join(path,'romfs')): return os.path.join(path,'romfs'),None
    return path,None

def check_romfs(base,update):
    """Problems with the chosen game folders (empty list = fine)."""
    problems=[]
    if not base or not os.path.isdir(os.path.join(base,'Banc')) or not os.path.isfile(os.path.join(base,'Pack','ZsDic.pack.zs')):
        problems.append('Base game RomFS not found (it should contain Banc and Pack/ZsDic.pack.zs).')
    if not update or not os.path.isdir(update):
        problems.append('Update RomFS not found. The randomizer needs update %s installed and dumped.'%SUPPORTED_VERSION)
    elif not glob.glob(os.path.join(update,'System','Resource','ResourceSizeTable.Product.111.*')):
        problems.append('The update RomFS is not version %s (expected ResourceSizeTable.Product.111).'%SUPPORTED_VERSION)
    if zst.BACKEND is None: problems.append('No zstd support: install Python 3.14+, or run: pip install zstandard')
    return problems

class Game:
    def __init__(self,dump=None,base=None,update=None):
        """Either a dump folder (with base/romfs and updates/<n>/romfs), or the base and update romfs folders."""
        if dump: base,update=find_romfs(dump)
        self.base,self.update=base,update
        self.dict_dir=os.path.join(PROJECT,'cache','dicts')
        if not os.path.exists(self.dict(BCETT_DICT)): self._extract_dicts()
    def dict(self,name): return os.path.join(self.dict_dir,name)
    def path(self,rel):
        """Full path of a romfs file; the update's copy wins over the base game's."""
        if self.update and os.path.exists(os.path.join(self.update,rel)): return os.path.join(self.update,rel)
        return os.path.join(self.base,rel)
    def _extract_dicts(self):
        os.makedirs(self.dict_dir,exist_ok=True)
        for name,data in sarc_files(zread(self.path('Pack/ZsDic.pack.zs'))).items():
            open(self.dict(name),'wb').write(data)
    def rstb_rel(self):
        for root in (self.update,self.base):
            if root:
                hits=glob.glob(os.path.join(root,'System','Resource','ResourceSizeTable.*.rsizetable.zs'))
                if hits: return os.path.relpath(hits[0],root).replace(os.sep,'/')
    def scene_files(self):
        """Relative paths of every scene (Banc/<Area>/<file>.bcett.byml.zs), base + update."""
        rels=set()
        for root in (self.base,self.update):
            if root: rels|={os.path.relpath(p,root).replace(os.sep,'/') for p in glob.glob(os.path.join(root,'Banc','*','*.bcett.byml.zs'))}
        return sorted(rels)
    def event_files(self):
        """Relative paths of every event flow (Event/EventFlow/*.bfevfl.zs), base + update."""
        rels=set()
        for root in (self.base,self.update):
            if root: rels|={os.path.relpath(p,root).replace(os.sep,'/') for p in glob.glob(os.path.join(root,'Event','EventFlow','*.bfevfl.zs'))}
        return sorted(rels)
    def read_scene(self,rel):
        from .bymlrw import read
        return read(zread(self.path(rel),self.dict(BCETT_DICT)))

def actor_hash(actor):
    h=actor.get('Hash'); return h.v if hasattr(h,'v') else h

def area_of(rel): return rel.split('/')[1]
