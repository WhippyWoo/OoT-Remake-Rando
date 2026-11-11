# Optional gameplay tweaks (randomizer options). Each adds the files it changes to a ModBuilder.
import os,struct
from .game import ZS_DICT,zread
from .sarc import sarc_file_offsets
from .bymlrw import read,write

def murmur3(key,seed=0):
    """Hash used by the game for save-data names and enum values."""
    key=key.encode(); h=seed; c1,c2=0xcc9e2d51,0x1b873593; n=len(key)//4
    for i in range(n):
        k=int.from_bytes(key[4*i:4*i+4],'little'); k=(k*c1)&0xffffffff; k=((k<<15)|(k>>17))&0xffffffff; k=(k*c2)&0xffffffff
        h^=k; h=((h<<13)|(h>>19))&0xffffffff; h=(h*5+0xe6546b64)&0xffffffff
    t=key[4*n:]; k=0
    for i,b in enumerate(t): k|=b<<(8*i)
    if t: k=(k*c1)&0xffffffff; k=((k<<15)|(k>>17))&0xffffffff; k=(k*c2)&0xffffffff; h^=k
    h^=len(key); h^=h>>16; h=(h*0x85ebca6b)&0xffffffff; h^=h>>13; h=(h*0xc2b2ae35)&0xffffffff; h^=h>>16; return h

LIFT_GRADE={n:murmur3(n) for n in ('None','Low','Middle','High')}

def _set_root_uint(byml,key,value):
    """Change an unsigned-int value in a little-endian BYML file's top-level dictionary, in place."""
    d=bytearray(byml); hk,root=struct.unpack_from('<I',d,4)[0],struct.unpack_from('<I',d,12)[0]
    n=int.from_bytes(d[hk+1:hk+4],'little'); keys=[d[hk+struct.unpack_from('<I',d,hk+4+4*i)[0]:].split(b'\0')[0].decode() for i in range(n)]
    for i in range(int.from_bytes(d[root+1:root+4],'little')):
        e=root+4+8*i
        if keys[int.from_bytes(d[e:e+3],'little')]==key:
            assert d[e+3]==0xD3, 'expected an unsigned int'
            old=struct.unpack_from('<I',d,e+4)[0]; struct.pack_into('<I',d,e+4,value); return bytes(d),old
    raise KeyError(key)

def bombs_without_bracelet(mod):
    """Bombs from the Bomb Bag can be used without the Goron Bracelet.
    The remake gives bombs lift grade 'Low' (the bracelet's grade); this sets them to 'None' like Bombchus.
    Bomb flowers have their own settings and still need the bracelet."""
    game=mod.game; rel='Pack/Actor/Item_Bomb.pack.zs'; pack=bytearray(zread(game.path(rel),game.dict('pack.zsdic')))
    start,end=sarc_file_offsets(bytes(pack))['Component/LiftableParam/Item_Bomb.game__component__LiftableParam.bgyml']
    new,old=_set_root_uint(pack[start:end],'LiftGrade',LIFT_GRADE['None'])
    assert old==LIFT_GRADE['Low'], 'unexpected bomb lift grade'
    pack[start:end]=new; mod.add_file(rel,bytes(pack),game.dict('pack.zsdic'),len(pack))

class SaveDefaults:
    """Edits starting values in the save-data list (GameData/GameDataList), i.e. what a new file begins with.
    Names are hashed with murmur3; quests ('Challenges') are enums named Step_<Quest>."""
    def __init__(self,mod):
        self.mod=mod; g=mod.game
        self.rel=[r for r in ('GameData/GameDataList.Product.110.byml.zs','GameData/GameDataList.Product.100.byml.zs') if os.path.exists(g.path(r))][0]
        self.raw=zread(g.path(self.rel),g.dict(ZS_DICT)); self.ver,self.root=read(self.raw)
        self.idx={}
        for table,entries in self.root.root['Data'].items():
            for e in entries:
                if isinstance(e,dict) and 'Hash' in e: self.idx[e['Hash'].v]=(table,e)
        self.changes=[]
    def _entry(self,name,table):
        t,e=self.idx.get(murmur3(name),(None,None))
        if t!=table: raise KeyError('%s is not a %s save value (found %s)'%(name,table,t))
        return e
    def set_bool(self,name,value=True):
        e=self._entry(name,'Bool'); e['DefaultValue']=bool(value); self.changes.append('%s=%s'%(name,value))
    def set_int(self,name,value):
        e=self._entry(name,'Int'); e['DefaultValue']=int(value); self.changes.append('%s=%s'%(name,value))
    def set_quest(self,quest,step):
        e=self._entry('Step_'+quest,'Enum'); steps=[str(x) for x in e['RawValues']]
        if step not in steps: raise KeyError('%s has no step %s'%(quest,step))
        e['DefaultValue'].v=murmur3(step); self.changes.append('quest %s=%s'%(quest,step))
    def give_item(self,item,count=1):
        self.set_bool('IsGet.'+item)
        if murmur3('PouchData.%s.StockNum'%item) in self.idx: self.set_int('PouchData.%s.StockNum'%item,count)
    def save(self):
        if not self.changes: return
        data=write(self.root,self.ver)
        assert read(data)[1].root['Data'].keys()==self.root.root['Data'].keys()
        self.mod.add_file(self.rel,data,self.mod.game.dict(ZS_DICT),len(self.raw))

def allow_skipping_all(mod):
    """Every cutscene becomes skippable. Only three use the shared DisableSkip setting (the opening intro
    Dm_Kokiri_0000, the title screen and the staff credits); this turns that setting off."""
    rel='Event/EventSetting/EventSettingComponent/SkipSetting/DisableSkip.engine__event__SkipSetting.bgyml'
    raw=open(mod.game.path(rel),'rb').read(); ver,r=read(raw)
    if r.get('IsDisableSkip'): r['IsDisableSkip']=False; mod.add_file(rel,write(r,ver),None,len(raw))

# Wake-up and house scenes only. The Deku Tree talk (Dm_Kokiri_0070/0075) is NOT skipped: it completes the
# Meet_DekuTree quest, and starting with that quest complete makes Mido and the early Kokiri leave while Mido's
# invisible wall (flag KokiriForest_Npc_Kokiri_Mido_Child_Blocker, cleared only by Mido's own event) stays up.
OPENING_SCENES=['Dm_Kokiri_0030','Dm_Kokiri_0045','Dm_Kokiri_0050','Dm_Kokiri_0060','Dm_Kokiri_0063']
def skip_opening(mod,save):
    """Opening: every cutscene becomes skippable (including the intro, title screen and credits), and the
    wake-up/house scenes count as played with their effect (Link's door open). The story quests are left alone,
    so Mido, the early Kokiri and the Deku Tree talk work as normal (the talk can be skipped with the button)."""
    allow_skipping_all(mod)
    for ev in OPENING_SCENES: save.set_bool('HavePlayedEvent.'+ev)
    save.set_bool('KokiriForest_LinkHouseDoor_Open'); save.set_bool('Dm_Kokiri_0050_After_Near_End')

def skip_owls(mod,save):
    """The forced owl cutscenes in Hyrule Field and Zora's River count as played. Owl talks that advance a quest
    (Zora's River) or fly Link somewhere (Lake Hylia, Death Mountain Trail) are kept."""
    for ev in ('Dm_HrlField_0030','Dm_HrlField_0040','Dm_ZoraRiver_0005'): save.set_bool('HavePlayedEvent.'+ev)

CASTLE_SCENES=['Dm_HrlCastle_0000','Dm_HrlCastle_0005','Dm_HrlCastle_0020','Dm_HrlCastle_0030','Dm_HrlCastle_0035','Dm_HrlCastle_0045',
               'Dm_HrlCastle_0050','Dm_HrlCastle_0060','Dm_HrlCastle_0070','Dm_MelodyGet_Zelda']
def skip_child_zelda(mod,save):
    """EXPERIMENTAL, not safe yet. Start with Zelda's Letter and Zelda's Lullaby, castle scenes counted as played.
    Tested problems: completing the castle quest (Goto_HyruleCastle) at the start removes Mido and the early Kokiri;
    completing it when leaving the Deku Tree skips the forest-exit steps and softlocks the exit Kokiri. The quest
    also gates Lon Lon Ranch/Epona (via Talon), and the DoorOfTime quest Zelda starts drives the Goron Ruby chain,
    so a proper skip has to replay that chain at the right moments."""
    for ev in CASTLE_SCENES: save.set_bool('HavePlayedEvent.'+ev)
    save.give_item('Item_ZeldaLetter'); save.give_item('Item_Melody_ZeldaLullaby')

def apply(mod,options):
    """Apply the chosen tweak options (names as in OPTIONS) to a ModBuilder."""
    save=SaveDefaults(mod)
    if 'bombs_without_bracelet' in options: bombs_without_bracelet(mod)
    if 'skip_opening' in options: skip_opening(mod,save)
    if 'skip_owls' in options: skip_owls(mod,save)
    if 'skip_child_zelda' in options: skip_child_zelda(mod,save)
    save.save(); return save.changes

OPTIONS=['bombs_without_bracelet','skip_opening','skip_owls','skip_child_zelda']
