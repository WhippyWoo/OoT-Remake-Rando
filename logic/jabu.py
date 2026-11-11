"""Logic for child Link through all three child dungeons. Goal: collect the three Spiritual Stones.

Builds on logic/dodongo.py and adds Jabu-Jabu's Belly (same layout as the N64 version, tested):
- Fixed gifts: King Dodongo (Goron's Ruby), the Silver Scale from the Zora diving game, and Ruto's Letter at the
  bottom of Lake Hylia (an Obj_Bottle_Letter actor in HyruleField_Child_Static; needs the Silver Scale).
- Zora's River needs explosives for child Link (as in OoTR); Zora's Domain also needs Zelda's Lullaby.
  Jabu-Jabu needs Ruto's Letter (King Zora moves; the bottle then holds a fish for Jabu).
- Inside: Boomerang and Compass chests appear after the room's fight; the Map chest needs the Boomerang (OoTR).
  The remake's extra chest (Octorok room) and Barinade also require the Boomerang (safe over-requirement).
- Unconfirmed chests in Zora's River and Zora's Domain are junk_only.
"""
from lib.logic import Location
from logic import forest,dodongo

SWORD,BOMBBAG,BRACELET=forest.SWORD,dodongo.BOMBBAG,dodongo.BRACELET
BOOMERANG='Item_Boomerang'; KD='Event_KingDodongo'; SCALE='Item_Scale_Silver'; LETTER='Item_Bottle_Letter'
JB='Jabu Jabus Belly'
SETTINGS=dodongo.SETTINGS        # same options as the dodongo world (bombs_without_bracelet)

zora_river=lambda s: dodongo.out_of_forest(s) and dodongo.explosives(s)
zora_domain=lambda s: zora_river(s) and s.has(dodongo.LULLABY) and s.has(dodongo.OCARINA)
jabu=lambda s: zora_domain(s) and s.has(LETTER)
jabu_boomerang=lambda s: jabu(s) and s.has(BOOMERANG)

GIFTS=[
    Location('King Dodongo',None,KD,dodongo.goal,fixed=True),
    Location('Zora Diving Game',None,SCALE,zora_domain,fixed=True),
    Location('Lake Hylia Underwater Bottle',474136620438465634,LETTER,lambda s: dodongo.out_of_forest(s) and s.has(SCALE),fixed=True),
]
JABU=[
    Location('Jabu Jabus Belly Boomerang Chest',5527401621172639818,BOOMERANG,jabu,region=JB),
    Location('Jabu Jabus Belly Compass Chest',3510516276638146208,'Item_Dungeon_Compass',jabu,region=JB),
    Location('Jabu Jabus Belly Map Chest',14933854942830098290,'Item_Dungeon_Map',jabu_boomerang,region=JB),
    Location('Jabu Jabus Belly Octorok Room Chest',3609242017501283521,'TBox_Rupee_Red',jabu_boomerang,region=JB),
]
UNCONFIRMED=[
    Location('ZR Seed Chest',8838426083116998768,'Item_ScrubBusinessSeed',zora_river,region='Zora River',junk_only=True),
    Location('ZD Torch Heart Piece Chest',3130048366421939233,'Obj_Heart_Piece',zora_domain,region='Zoras Domain',junk_only=True),
]
LOCATIONS=dodongo.LOCATIONS+GIFTS+JABU+UNCONFIRMED
PROGRESSION=dodongo.PROGRESSION+[BOOMERANG]
RESTRICTED=dodongo.RESTRICTED+[('Item_Dungeon_Map',lambda l:l.region==JB),('Item_Dungeon_Compass',lambda l:l.region==JB)]
AREAS=dodongo.AREAS+('ZoraRiver','ZoraDomain','InsideJabuJabuBelly')
def goal(state):   # Queen Gohma, King Dodongo, Barinade
    return forest.goal(state) and state.has(KD) and jabu_boomerang(state) and state.has(SWORD)
