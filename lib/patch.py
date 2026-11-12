# Builds a mod folder: changes chest contents in scene files and keeps the resource size table in step.
import os
from .game import TITLE_ID,BCETT_DICT,ZS_DICT,zread,zwrite,actor_hash,area_of
from .evfl import Evfl,EvflWriter
from .bymlrw import write
from .rstb import Rstb
from . import progressive

# Chest events that belong to the item, not the place: removed when the item leaves its chest
# (moving them with the item teleports Link into the original chest's cutscene). They only add an item tutorial,
# a Navi tip or a camera shot. Chest events that move the story or a quest on (Nabooru taken away, Serenade of
# Water, the Ice Arrow quest, Ruto in Jabu-Jabu, Dampe's race, minigames) stay with the place.
ITEM_EVENTS={'Get_StoneOfForest_GetSword','Get_StoneOfFire_GetBombBag','ForestTemple_GetBow','FireTemple_GetHammer',
             'BottomOfTheWell_GetGlassTruth','SageOfShdawo_GetHoverBoots','SageOfSpirit_GetShield',
             'InsideGanonCastle_Get_Gauntlet_Gold','WaterTemple_Room07_LongHook_FocusOnGimmick','InsideTheDekuTree_GetSlingShot',
             'ForesetTemple_GetBossKey',   # 'Foreset' is Nintendo's spelling
             'InsideTheDekuTree_GetMap','InsideTheDekuTree_GetCompass','DodongoCavern_GetMap','DodongoCavern_GetCompass',
             'ForesetTemple_GetMap','ForesetTemple_GetCompass','FireTemple_GetMap','FireTemple_GetCompass',
             'WaterTemple_GetMap','WaterTemple_GetCompass','ShadowTemple_GetMap','ShadowTemple_GetCompass',
             'SpiritTemple_GetCompass','BottomOfTheWell_GetCompass'}

# Chest variants with the substitute check (see ModBuilder.set_chest_item)
SUBSTITUTE_CHEST={'Obj_TBox_A_01':'Obj_TBox_A_06','Obj_TBox_A_01_NoBake':'Obj_TBox_A_06_NoBake',
                  'Obj_TBox_A_06':'Obj_TBox_A_06','Obj_TBox_A_06_NoBake':'Obj_TBox_A_06_NoBake'}
SUBSTITUTE_KEYS=('Drop__CheckActor','Drop__DropActor_Substitute')

class ModBuilder:
    def __init__(self,game,out_dir,name,areas=None,romfs_dir=None):
        """Writes to <out_dir>/mods/<title id>/<name>/romfs, or to romfs_dir if given."""
        self.game=game; self.mod=romfs_dir or os.path.join(out_dir,'mods',TITLE_ID,name,'romfs')
        self.scenes={}; self.changed=set(); self.extra={}; self.three_tier=False; self.grow={}; self.events={}
        for rel in game.scene_files():
            if areas is None or area_of(rel) in areas: self.scenes[rel]=game.read_scene(rel)
    def set_chest_item(self,hash,item,upgrade=None):
        """Put `item` in the chest with this Hash in every scene file it appears in (child + adult copies).
        upgrade=(tier 1, tier 2[, tier 3]): a progressive item; the chest gives the first tier Link doesn't have.
        This uses the game's own "substitute" chest (Obj_TBox_A_06, normally a Deku Shield chest that gives rupees
        once you own the shield); the chest becomes that variant. A moved item also clears an existing substitute,
        or a Deku Shield chest would hand out rupees instead of the randomized item."""
        hits=0
        for rel,(ver,root) in self.scenes.items():
            for a in root.get('Actors',[]):
                if actor_hash(a)!=hash: continue
                dyn=a['Dynamic']; hits+=1
                if dyn['Drop__DropActor']==item and not upgrade: continue
                dyn['Drop__DropActor']=item; self.changed.add(rel)
                if dyn.get('GetEventName') in ITEM_EVENTS: del dyn['GetEventName']
                for k in SUBSTITUTE_KEYS: dyn.pop(k,None)
                if upgrade:
                    if a['Gyaml'] not in SUBSTITUTE_CHEST: raise ValueError('%s (%d) has no substitute variant'%(a['Gyaml'],hash))
                    a['Gyaml']=SUBSTITUTE_CHEST[a['Gyaml']]
                    dyn['Drop__CheckActor'],dyn['Drop__DropActor_Substitute']=upgrade[0],upgrade[1]
                    if len(upgrade)==3:   # third tier: from the chest graph patched by progressive.py
                        if progressive.NEXT_TIER.get(upgrade[1])!=upgrade[2]: raise ValueError('unknown tier chain %r'%(upgrade,))
                        self.three_tier=True
        if not hits: raise KeyError('no chest with hash %d'%hash)
    def set_gift_item(self,steps,item):
        """Change what an event hands out: every step ('Flow#event:routine:parameter') gets `item`."""
        for step in steps:
            tag,_,param=step.split(':'); flow,idx=tag.split('#'); rel='Event/EventFlow/%s.bfevfl.zs'%flow
            if rel not in self.events:
                raw=zread(self.game.path(rel),self.game.dict(ZS_DICT)); self.events[rel]=(Evfl(raw),EvflWriter(raw))
            f,w=self.events[rel]; ev=f.events[int(idx)]
            off,_=f.param_ref(f.q(ev['off']+0x10),param); w.set_string(off,item)
    def _chest_info(self):
        if not hasattr(self,'_info'):
            self._info={}   # hash -> (all copies have a substitute variant, area)
            for rel,(ver,root) in self.scenes.items():
                for a in root.get('Actors',[]):
                    h=actor_hash(a); ok,_=self._info.get(h,(True,None))
                    self._info[h]=(ok and a.get('Gyaml') in SUBSTITUTE_CHEST,area_of(rel))
        return self._info
    def can_substitute(self,hash):
        """Whether every copy of this chest has a substitute variant (small chests; not big or Lens of Truth ones)."""
        return self._chest_info().get(hash,(False,None))[0]
    def chest_area(self,hash): return self._chest_info().get(hash,(False,None))[1]
    def grow_entry(self,key,old_size,new_size):
        """A file inside a pack changed size: its own size table entry (the game loads it on its own budget) grows too."""
        if new_size>old_size: self.grow[key]=max(self.grow.get(key,0),new_size-old_size)
    def add_file(self,rel,data,dict_=None,original_size=None):
        """Any other changed file (event settings, save-data list, actor packs). Files ending in .zs are compressed.
        original_size: the unmodified file's size, so its size table entry can grow by the same amount."""
        self.extra[rel]=(data,dict_,original_size)
    def build(self):
        if self.three_tier: progressive.three_tier_chests(self)
        rstb_rel=self.game.rstb_rel(); rstb=Rstb(zread(self.game.path(rstb_rel)))
        for rel,(data,dict_,orig) in self.extra.items():
            out=os.path.join(self.mod,rel)
            if rel.endswith('.zs'): zwrite(data,out,dict_)
            else: os.makedirs(os.path.dirname(out),exist_ok=True); open(out,'wb').write(data)
            key=rel[:-3] if rel.endswith('.zs') else rel; old=rstb.get(key)
            if old is not None and orig is not None and len(data)>orig: rstb.set(key,old+((len(data)-orig+31)&~31))
        for rel,(f,w) in self.events.items():
            data=w.build(); zwrite(data,os.path.join(self.mod,rel),self.game.dict(ZS_DICT))
            need=((len(data)+31)&~31)+272       # size table rule for event files
            if need>(rstb.get(rel[:-3]) or 0): rstb.set(rel[:-3],need)
        for key,extra in self.grow.items():
            old=rstb.get(key)
            if old is None: raise KeyError('no size table entry for '+key)
            rstb.set(key,old+((extra+31)&~31))
        for rel in sorted(self.changed):
            ver,root=self.scenes[rel]; data=write(root,ver)
            zwrite(data,os.path.join(self.mod,rel),self.game.dict(BCETT_DICT))
            need=((len(data)+31)&~31)+264       # size table rule for scene files
            if need>rstb.get(rel[:-3]): rstb.set(rel[:-3],need)
        zwrite(rstb.build(),os.path.join(self.mod,rstb_rel))
        return self.mod
