"""Items handed out by NPCs and minigames (events) that can be shuffled. Batch 1: one-off items given through the
shared item-handover routines, whose events don't check the vanilla item anywhere else.
Not yet: upgrades with tiers (bags, quivers, wallets, scales, Goron Bracelet), songs, medallions, stones and story
items, trade items, Great Fairies, bottles that come filled, Dampe's dig (the heart piece is an object in the ground).
Steps are 'Flow#event:routine:parameter' (tools/gift_locations.py lists them all)."""
from lib.logic import Location

def G(name,vanilla,region,*steps): return Location(name,None,vanilla,region=region,gift=steps)
GIFTS=[
    G('Market Bombchu Bowling Heart Piece','Obj_Heart_Piece','Market','MiniGame_BombchuBowling#296:NpcCommon_HandOver_NpcToPlayer_NoDisplay:ReveiveItem'),
    G('Market Lost Dog Heart Piece','Obj_Heart_Piece','Market','SubEvent_FindRichard#35:NpcCommon_HandOver_NpcToPlayer_NoDisplay:ReveiveItem'),
    G('Market Poe Collector Bottle','Item_Bottle','Market','Npc_Hylia_048_BottleShop#319:GetInEvent_Poeshop:ActorName'),
    G('Kakariko Anju Cucco Bottle','Item_Bottle','KakarikoVillage','Minigame_CatchCucco#124:NpcCommon_HandOver_NpcToPlayer_NoDisplay:ReveiveItem'),
    G('Kakariko Adult Villager Heart Piece','Obj_Heart_Piece','KakarikoVillage','Npc_Hylia_001_Adult#14:GetInEvent:ActorName'),
    G('Skulltula House Stone of Agony','Item_AgonyStone','KakarikoVillage','GatheringTokenGold#246:TakenReward_Common_Event:TakenRewardActor'),
    G('Skulltula House Bombchus','Item_BombchuBundle_Large','KakarikoVillage','GatheringTokenGold#248:TakenReward_Common_Event:TakenRewardActor'),
    G('Skulltula House Heart Piece','Obj_Heart_Piece','KakarikoVillage','GatheringTokenGold#249:TakenReward_Common_Event:TakenRewardActor'),
    G('Lost Woods Skull Kid Heart Piece','Obj_Heart_Piece','LostWood','Npc_SkullKid_Child#62:GetInEvent_NotTurn_NotNpc:ActorName'),
    G('Lost Woods Memory Game Heart Piece','Obj_Heart_Piece','LostWood','Npc_SkullKid_Child_02#203:GetInEvent_NotTurn_NotNpc:ActorName'),
    G('Lake Hylia Lab Heart Piece','Obj_Heart_Piece','HyruleField','Npc_Hylia_045_Child#55:NpcCommon_HandOver_NpcToPlayer_NoDisplay:ReveiveItem'),
    G('Lake Hylia Fishing Heart Piece','Obj_Heart_Piece','HyruleField',
      'MiniGame_Fishing#482:NpcCommon_HandOver_NpcToPlayer_NoDisplay:ReveiveItem','MiniGame_Fishing#489:GetInEvent_NotTurn:ActorName'),
    G('Gerudo Horseback Archery Heart Piece','Obj_Heart_Piece','GerudoFortress','Minigame_HorsebackArchery#313:GetInEvent_NotTurn_PosCamera:ActorName'),
]
