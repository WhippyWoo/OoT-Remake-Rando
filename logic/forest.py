"""Logic for the first mini-seed: Kokiri Forest (child) and the Deku Tree. Goal: defeat Queen Gohma.

Rules follow the N64 randomizer (OoTR) for these areas, kept conservative:
- Mido blocks the Deku Tree until Link has the Kokiri Sword and a Deku Shield (he checks the game's
  IsGet.Weapon_Sword_Kokiri / IsGet.Weapon_Shield_Deku flags). The shield is sold in the Kokiri shop,
  so only the sword is a randomized requirement.
- The Slingshot is needed to reach Queen Gohma (eye switch / basement).
- Remake difference: the wall Skulltulas on the vines up to the 3rd floor (Compass room) are placed so the climb
  needs the Slingshot (tested in game). In the N64 version that room is free.
Deku Sticks and Nuts are sold in the Kokiri shop, so they're treated as always available.
Three chests whose exact spot isn't confirmed yet stay vanilla.
"""
from lib.logic import Location

SWORD='Item_Sword_Kokiri'; SLINGSHOT='Item_Range_SlingShot'
deku=lambda s: s.has(SWORD)
deku_3f=lambda s: s.has(SWORD) and s.has(SLINGSHOT)   # vine climb past wall Skulltulas
KF,DT='Kokiri Forest','Deku Tree'

LOCATIONS=[
    Location("KF Mido's House Chest 1",10831981390482426294,'TBox_Rupee_Green',region=KF),
    Location("KF Mido's House Chest 2",4555665598794293658,'TBox_Rupee_Blue',region=KF),
    Location("KF Mido's House Chest 3",9725242744547055868,'TBox_Rupee_Blue',region=KF),
    Location("KF Mido's House Chest 4",12786193094758345086,'TBox_Rupee_Blue',region=KF),
    Location('KF Kokiri Sword Chest',16757992849254467386,SWORD,region=KF),
    Location('Deku Tree Map Chest',8579518566955184384,'Item_Dungeon_Map',deku,region=DT),
    Location('Deku Tree Compass Chest',9284193025315608699,'Item_Dungeon_Compass',deku_3f,region=DT),
    Location('Deku Tree Compass Room Side Chest',11368028582977069031,'TBox_DekuNutBundle',deku_3f,region=DT),
    Location('Deku Tree Slingshot Chest',821372075822700622,SLINGSHOT,deku,region=DT),
    Location('Deku Tree Slingshot Room Side Chest',13027331340815880287,'TBox_DekuNutBundle',deku,region=DT),
    Location('Deku Tree Basement Chest',12889104996486369065,'Item_DekuStickBundle_Small',deku,region=DT),
]
PROGRESSION=[SWORD,SLINGSHOT]
# dungeon Map/Compass stay in their dungeon (the item is generic and counts for the dungeon you're in)
RESTRICTED=[('Item_Dungeon_Map',lambda l:l.region==DT),('Item_Dungeon_Compass',lambda l:l.region==DT)]
AREAS=('KokiriForest','InsideTheDekuTree')
SETTINGS={}   # no options affect this world
def goal(state): return state.has(SWORD) and state.has(SLINGSHOT)   # Queen Gohma
