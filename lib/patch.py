# Builds a mod folder: changes chest contents in scene files and keeps the resource size table in step.
import os
from .game import TITLE_ID,BCETT_DICT,zread,zwrite,actor_hash,area_of
from .bymlrw import write
from .rstb import Rstb

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
        self.scenes={}; self.changed=set(); self.extra={}
        for rel in game.scene_files():
            if areas is None or area_of(rel) in areas: self.scenes[rel]=game.read_scene(rel)
    def set_chest_item(self,hash,item,upgrade=None):
        """Put `item` in the chest with this Hash in every scene file it appears in (child + adult copies).
        upgrade=(have, better): the chest gives `better` instead if Link already has `have` (progressive items).
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
                    dyn['Drop__CheckActor'],dyn['Drop__DropActor_Substitute']=upgrade
        if not hits: raise KeyError('no chest with hash %d'%hash)
    def can_substitute(self,hash):
        """Whether every copy of this chest has a substitute variant (small chests; not big or Lens of Truth ones)."""
        if not hasattr(self,'_substitute'):
            self._substitute={}
            for ver,root in self.scenes.values():
                for a in root.get('Actors',[]):
                    h=actor_hash(a); self._substitute[h]=self._substitute.get(h,True) and a.get('Gyaml') in SUBSTITUTE_CHEST
        return self._substitute.get(hash,False)
    def add_file(self,rel,data,dict_=None,original_size=None):
        """Any other changed file (event settings, save-data list, actor packs). Files ending in .zs are compressed.
        original_size: the unmodified file's size, so its size table entry can grow by the same amount."""
        self.extra[rel]=(data,dict_,original_size)
    def build(self):
        rstb_rel=self.game.rstb_rel(); rstb=Rstb(zread(self.game.path(rstb_rel)))
        for rel,(data,dict_,orig) in self.extra.items():
            out=os.path.join(self.mod,rel)
            if rel.endswith('.zs'): zwrite(data,out,dict_)
            else: os.makedirs(os.path.dirname(out),exist_ok=True); open(out,'wb').write(data)
            key=rel[:-3] if rel.endswith('.zs') else rel; old=rstb.get(key)
            if old is not None and orig is not None and len(data)>orig: rstb.set(key,old+((len(data)-orig+31)&~31))
        for rel in sorted(self.changed):
            ver,root=self.scenes[rel]; data=write(root,ver)
            zwrite(data,os.path.join(self.mod,rel),self.game.dict(BCETT_DICT))
            need=((len(data)+31)&~31)+264       # size table rule for scene files
            if need>rstb.get(rel[:-3]): rstb.set(rel[:-3],need)
        zwrite(rstb.build(),os.path.join(self.mod,rstb_rel))
        return self.mod
