# Checks a built mod against the original game files (used by verify.py and the GUI).
import os,copy,glob
from .game import BCETT_DICT,zread,actor_hash
from .bymlrw import read
from .rstb import Rstb
from .sarc import sarc_files
from .patch import ITEM_EVENTS,SUBSTITUTE_CHEST,SUBSTITUTE_KEYS
from .logic import State,reachable,progressive
from . import zst

def check_files(game,mod,problems):
    """Every changed scene differs only in chest contents (and removed item-specific chest events, cleared or
    added substitute checks); compressed
    headers carry the uncompressed size; size table entries cover the new files. Returns ({chest hash: item}, n files)."""
    rstb_rel=game.rstb_rel(); rstb_path=os.path.join(mod,rstb_rel)
    if not zst.frame_ok(open(rstb_path,'rb').read(5),False): problems.append('bad compression header: '+rstb_rel)
    new_rstb=Rstb(zread(rstb_path))
    items={}; files=sorted(glob.glob(os.path.join(mod,'Banc','*','*.bcett.byml.zs')))
    for path in files:
        rel=os.path.relpath(path,mod).replace(os.sep,'/')
        if not zst.frame_ok(open(path,'rb').read(5),True): problems.append('bad compression header: '+rel)
        raw=zread(path,game.dict(BCETT_DICT)); _,new=read(raw); _,old=game.read_scene(rel)
        if len(new['Actors'])!=len(old['Actors']): problems.append('actor count changed: '+rel); continue
        for a,b in zip(new['Actors'],old['Actors']):
            if a==b: continue
            x=copy.deepcopy(a); y=copy.deepcopy(b); dx=x.get('Dynamic',{}); dy=y.get('Dynamic',{})
            if 'Drop__DropActor' not in dx: problems.append('non-chest actor changed in '+rel); continue
            items[actor_hash(a)]=dx['Drop__DropActor']
            dx.pop('Drop__DropActor'); dy.pop('Drop__DropActor',None)
            if dy.get('GetEventName') in ITEM_EVENTS and 'GetEventName' not in dx: dy.pop('GetEventName')
            for k in SUBSTITUTE_KEYS:   # cleared, or set for a progressive item (with the substitute chest variant)
                if k not in dx: dy.pop(k,None)
                elif SUBSTITUTE_CHEST.get(y['Gyaml'])==x['Gyaml']: dy[k]=dx[k]
            if SUBSTITUTE_CHEST.get(y['Gyaml'])==x['Gyaml']: y['Gyaml']=x['Gyaml']
            if x!=y: problems.append('chest changed beyond item/event in %s (%s)'%(rel,actor_hash(a)))
        for a in new['Actors']:
            if 'Drop__DropActor' in (a.get('Dynamic') or {}): items.setdefault(actor_hash(a),a['Dynamic']['Drop__DropActor'])
        if new_rstb.get(rel[:-3])<((len(raw)+31)&~31)+264: problems.append('size table entry too small: '+rel)
    # changed packs: the pack and every file in it that grew need bigger size table entries
    old_rstb=Rstb(zread(game.path(rstb_rel)))
    for path in sorted(glob.glob(os.path.join(mod,'Pack','**','*.pack.zs'),recursive=True)):
        rel=os.path.relpath(path,mod).replace(os.sep,'/'); d=game.dict('pack.zsdic')
        if not zst.frame_ok(open(path,'rb').read(5),True): problems.append('bad compression header: '+rel)
        new,old=zread(path,d),zread(game.path(rel),d)
        sizes=[(rel[:-3],len(old),len(new))]
        of,nf=sarc_files(old),sarc_files(new)
        sizes+=[(n,len(of.get(n,b'')),len(nf[n])) for n in nf if len(nf[n])!=len(of.get(n,b''))]
        for key,a,b in sizes:
            if b>a and old_rstb.get(key) is not None and new_rstb.get(key)<old_rstb.get(key)+(b-a): problems.append('size table entry too small: '+key)
    return items,len(files)

def check_logic(world,items,problems):
    """Reading the chest contents back from the mod: the goal is reachable, dungeon Maps/Compasses are in their
    dungeon, and no progression item sits in a junk-only chest. world.SETTINGS must match the seed's options."""
    placed={l.name:(l.vanilla if l.fixed else progressive(items.get(l.hash,l.vanilla))) for l in world.LOCATIONS}   # unchanged files keep vanilla items
    final,_=reachable(world.LOCATIONS,State(),placed)
    if not world.goal(final): problems.append('logic replay: goal NOT reachable')
    for it,allowed in world.RESTRICTED:
        if not any(placed[l.name]==it and allowed(l) for l in world.LOCATIONS): problems.append(it+' outside its dungeon')
    for l in world.LOCATIONS:
        if l.junk_only and placed[l.name] in world.PROGRESSION: problems.append('progression item in junk-only chest: '+l.name)
