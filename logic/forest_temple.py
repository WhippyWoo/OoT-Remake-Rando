"""Logic for child Link through to adult Link's first dungeon. Goal: defeat Phantom Ganon.

Builds on logic/jabu.py and adds:
- Time travel as fixed events: with the three Spiritual Stones, Zelda leaves the Ocarina of Time and the Song of
  Time at the castle moat (Dm_MelodyGet_Time); with those, the Door of Time opens and the Master Sword makes Link
  adult. Every adult-only location requires the Master Sword event (Link can switch ages freely after that).
- The Forest Temple (needs the Hookshot from Sacred Forest Meadow, as in OoTR). Small keys and the Boss Key stay
  vanilla (fixed) until key logic exists; the Map and Compass stay in the temple.
  Without the Bow: the first room, first Stalfos and Bow chests. Everything else, and Phantom Ganon, also requires
  the Bow (safe over-requirement: Poes and eye switches).
- Dampé's race (adult): the Hookshot chest. The other race chests and the Hyrule Field Poe/note chests are junk_only.
"""
from lib.logic import Location
from logic import forest,dodongo,jabu

SWORD=forest.SWORD; HOOKSHOT='Item_Hookshot'; BOW='Item_Range_Bow'
STONES=('Event_QueenGohma','Event_KingDodongo','Event_Barinade')
OOT='Item_Ocarina_Time'; SOT='Item_Melody_TimeSong'; ADULT='Event_MasterSword'
FT='Forest Temple'
SETTINGS=jabu.SETTINGS

adult=lambda s: s.has(ADULT)
forest_temple=lambda s: adult(s) and s.has(HOOKSHOT)
ft_bow=lambda s: forest_temple(s) and s.has(BOW)

GIFTS=[
    Location('Barinade',None,'Event_Barinade',lambda s: jabu.goal(s),fixed=True),
    Location('Zelda at the Castle Moat',None,OOT,lambda s: all(s.has(x) for x in STONES),fixed=True),
    Location('Song of Time',None,SOT,lambda s: s.has(OOT),fixed=True),
    Location('Master Sword Pedestal',None,ADULT,lambda s: s.has(OOT) and s.has(SOT) and all(s.has(x) for x in STONES),fixed=True),
]
FOREST_TEMPLE=[
    Location('Forest Temple First Room Chest',1171460703078800858,'Item_Dungeon_SmallKey',forest_temple,region=FT,fixed=True),
    Location('Forest Temple First Stalfos Chest',14776684749746592758,'Item_Dungeon_SmallKey',forest_temple,region=FT,fixed=True),
    Location('Forest Temple Bow Chest',11082303891540711688,BOW,forest_temple,region=FT),
    Location('Forest Temple Map Chest',3174893090599461927,'Item_Dungeon_Map',ft_bow,region=FT),
    Location('Forest Temple Well Chest',6449977980406424425,'Item_Dungeon_SmallKey',ft_bow,region=FT,fixed=True),
    Location('Forest Temple Eye Switch Chest',3433400840978782007,'Item_Dungeon_SmallKey',ft_bow,region=FT,fixed=True),
    Location('Forest Temple Blue Poe Chest',6948525240950728236,'Item_Dungeon_Compass',ft_bow,region=FT),
    Location('Forest Temple Floormaster Chest',7535137041266964235,'Item_Dungeon_SmallKey',ft_bow,region=FT,fixed=True),
    Location('Forest Temple Block Room Chest',15920957434854338961,'TBox_Rupee_Purple',ft_bow,region=FT),
    Location('Forest Temple Basement Chest',9038700938965170329,'TBox_ArrowBundle_Large',ft_bow,region=FT),
    Location('Forest Temple Boss Key Chest',5306318520835485827,'Item_Dungeon_BossKey',ft_bow,region=FT,fixed=True),
]
DAMPE=[Location('Graveyard Dampe Race Hookshot Chest',16041366920820397198,HOOKSHOT,adult,region='Graveyard')]
J=lambda name,hash,item,region: Location(name,hash,item,adult,region=region,junk_only=True)
UNCONFIRMED=[
    J('Graveyard Dampe Race Heart Piece Chest',5534919361313859554,'Obj_Heart_Piece','Graveyard'),
    J('Graveyard Dampe Race Red Rupee Chest',234006393181394602,'TBox_Rupee_Red','Graveyard'),
    J('Graveyard Dampe Race Blue Rupee Chest',4322670163630771947,'TBox_Rupee_Blue','Graveyard'),
    J('HF Poe Note 04 Chest',9891111455604007674,'TBox_Rupee_Red','Hyrule Field'),
    J('HF Poe Note 06 Chest',17023457248274633121,'TBox_Rupee_Red','Hyrule Field'),
    J('HF Poe Note 08 Chest',1163740567397714729,'TBox_Rupee_Red','Hyrule Field'),
]
LOCATIONS=jabu.LOCATIONS+GIFTS+FOREST_TEMPLE+DAMPE+UNCONFIRMED
PROGRESSION=jabu.PROGRESSION+[HOOKSHOT,BOW]
RESTRICTED=jabu.RESTRICTED+[('Item_Dungeon_Map',lambda l:l.region==FT),('Item_Dungeon_Compass',lambda l:l.region==FT)]
AREAS=jabu.AREAS+('ForestTemple',)
def goal(state): return ft_bow(state)   # Phantom Ganon (Boss Key is vanilla in the temple)
