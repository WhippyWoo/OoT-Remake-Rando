"""Logic for child Link from Kokiri Forest to King Dodongo. Goal: defeat King Dodongo.

Builds on logic/forest.py (Kokiri Forest + Deku Tree) and adds:
- Vanilla gifts as fixed events (not randomized yet): Queen Gohma, Fairy Ocarina, Zelda's Letter,
  Zelda's Lullaby, Saria's Song, Goron Bracelet. Leaving Kokiri Forest needs Queen Gohma beaten.
- Dodongo's Cavern. Layout is the same as the N64 version (tested); the remake adds chests, including one
  that appears after each of the two Lizalfos fights (rooms 5 and 16). The guide confirms the Map and Compass chests open with bomb flowers (Goron Bracelet)
  and the Bomb Bag chest needs the Slingshot for the eye switches. Every other chest in the dungeon, and
  King Dodongo, also require the Bomb Bag: over-requiring is always safe, it only narrows where items go.
- Remake difference (tested in game): bombs only work with the Goron Bracelet. Without it Link pulls a
  bomb out and puts it straight back. So "can use bombs" means Bomb Bag + Goron Bracelet, unless the
  bombs_without_bracelet option is on (see lib/tweaks.py).
- Chests in the areas on the way (Lost Woods, Sacred Forest Meadow, Hyrule Field, Kakariko, Graveyard,
  Death Mountain Trail, Goron City) whose requirements aren't confirmed are junk_only. Adult-only and
  both-ages chests are left out entirely.
"""
from lib.logic import Location
from logic import forest

SWORD,SLINGSHOT=forest.SWORD,forest.SLINGSHOT
BOMBBAG='Item_BombBag_Small'
GOHMA='Event_QueenGohma'; OCARINA='Item_Ocarina_Fairy'; LETTER='Item_ZeldaLetter'
LULLABY='Item_Melody_ZeldaLullaby'; SARIA='Item_Melody_SariaSong'; BRACELET='Item_Gauntlet_Goron'
DC='Dodongos Cavern'

out_of_forest=lambda s: s.has(GOHMA)
dc=lambda s: s.has(BRACELET)                  # Bracelet implies the whole gift chain before it
SETTINGS={'bombs_without_bracelet':False}
explosives=lambda s: s.has(BOMBBAG) and (SETTINGS['bombs_without_bracelet'] or s.has(BRACELET))
dc_bombs=lambda s: dc(s) and explosives(s)

GIFTS=[
    Location('Queen Gohma',None,GOHMA,forest.goal,fixed=True),
    Location('Saria at the Bridge',None,OCARINA,out_of_forest,fixed=True),
    Location('Zelda',None,LETTER,out_of_forest,fixed=True),
    Location('Impa',None,LULLABY,lambda s: s.has(LETTER),fixed=True),
    Location('Saria in Sacred Forest Meadow',None,SARIA,lambda s: s.has(LETTER) and s.has(OCARINA),fixed=True),
    Location('Darunia',None,BRACELET,lambda s: s.has(LETTER) and s.has(OCARINA) and s.has(LULLABY) and s.has(SARIA),fixed=True),
]
DODONGO=[
    Location('Dodongos Cavern Map Chest',8291119063305855945,'Item_Dungeon_Map',dc,region=DC),
    Location('Dodongos Cavern Compass Chest',17531994809974271603,'Item_Dungeon_Compass',dc,region=DC),
    Location('Dodongos Cavern Bomb Bag Chest',12161709650443144121,BOMBBAG,lambda s: dc(s) and s.has(SLINGSHOT),region=DC),
    Location('Dodongos Cavern Lobby Deku Shield Chest',7524527082521156886,'TBox_Shield_Deku',dc_bombs,region=DC),
    Location('Dodongos Cavern Lobby Rupee Chest',8607798771661947511,'TBox_Rupee_Blue',dc_bombs,region=DC),
    Location('Dodongos Cavern Room 10 Seed Chest',12253889300578348965,'Item_ScrubBusinessSeed',dc_bombs,region=DC),
    Location('Dodongos Cavern Room 13 Deku Shield Chest',11582649900854566065,'TBox_Shield_Deku',dc_bombs,region=DC),
    Location('Dodongos Cavern Lizalfos Fight 1 Chest',7764016096998075927,'TBox_Rupee_Red',dc_bombs,region=DC),
    Location('Dodongos Cavern Lizalfos Fight 2 Chest',850464708089653824,'Item_ScrubBusinessSeed',dc_bombs,region=DC),
]
J=lambda name,hash,item,region: Location(name,hash,item,out_of_forest,region=region,junk_only=True)
UNCONFIRMED=[
    Location('KF Chest near Bridge Scrubs',4349272251343787229,'TBox_Rupee_Purple',region='Kokiri Forest',junk_only=True),
    Location('KF Grotto Chest (Deku Brothers)',14818888396401495482,'TBox_Rupee_Green',region='Kokiri Forest',junk_only=True),
    J('LW Chest near Scrubs',17479747339356189279,'TBox_Rupee_Purple','Lost Woods'),
    J('SFM Seed Chest (Song of Time blocks)',1764383515296652106,'Item_ScrubBusinessSeed','Sacred Forest Meadow'),
    J('SFM Wolfos Grotto Chest',7995233962349162969,'TBox_Rupee_Purple','Sacred Forest Meadow'),
    J('HF Seed Chest',17445672702269453589,'Item_ScrubBusinessSeed','Hyrule Field'),
    J('HF ReDead Grotto Chest',5755485285664292988,'TBox_Rupee_Purple','Hyrule Field'),
    J('HF Candle Grotto Chest',6900843020594897860,'TBox_Rupee_Red','Hyrule Field'),
    J('Kakariko Grotto Chest',12902291359202819102,'TBox_Rupee_Blue','Kakariko Village'),
    J('Graveyard Shield Grave Chest',16912540161937823130,'TBox_Shield_Hylian','Graveyard'),
    J('Graveyard Heart Piece Grave Chest',9622128545943056087,'Obj_Heart_Piece','Graveyard'),
    J('DMT Seed Chest',9809508929088891725,'Item_ScrubBusinessSeed','Death Mountain Trail'),
    J('Goron City Maze Chest 1',4402942101476009858,'TBox_Rupee_Red','Goron City'),
    J('Goron City Maze Chest 2',1176975953041865014,'TBox_Rupee_Blue','Goron City'),
    J('Goron City Maze Chest 3',14647422914070455120,'TBox_Rupee_Blue','Goron City'),
    J('Goron City Maze Chest 4',3870071239709713434,'TBox_Rupee_Purple','Goron City'),
    J('Goron City Lower Chest 1',9159710900681116662,'TBox_Rupee_Green','Goron City'),
    J('Goron City Lower Chest 2',10944569637726152230,'TBox_Rupee_Purple','Goron City'),
]
LOCATIONS=forest.LOCATIONS+GIFTS+DODONGO+UNCONFIRMED
PROGRESSION=[SWORD,SLINGSHOT,BOMBBAG]
RESTRICTED=forest.RESTRICTED+[('Item_Dungeon_Map',lambda l:l.region==DC),('Item_Dungeon_Compass',lambda l:l.region==DC)]
AREAS=('KokiriForest','InsideTheDekuTree','LostWood','SacredForestMeadow','HyruleField','KakarikoVillage','Graveyard',
       'DeathMountainTrail','GoronCity','DodongoCavern')
def goal(state): return dc_bombs(state) and state.has(SWORD)   # King Dodongo
