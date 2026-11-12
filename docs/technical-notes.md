# Technical notes

How the randomizer works and what was found while building it. The README covers using and building it.

## Options in detail
Pass these to `logic_seed.py`, or build them on their own with `python tweaks_mod.py --skip-opening ...` (no randomization).
| Option | What it does |
|---|---|
| `--bombs-without-bracelet` | Bombs work without the Goron Bracelet. The remake gives bombs lift grade `Low` (the bracelet's); this sets it to `None` like Bombchus. One value in `Pack/Actor/Item_Bomb.pack.zs`, same file size. Bomb flowers still need the bracelet. |
| `--skip-opening` | All cutscenes become skippable (only the intro, title screen and credits weren't). The wake-up and house scenes count as played, with their effect (Link's door open). Story quests are left alone: starting `Meet_DekuTree` as Complete (tested) makes Mido and the early Kokiri leave while Mido's invisible wall stays, so the Deku Tree talk plays normally (skippable). |
| `--skip-owls` | The forced owl cutscenes (`Dm_HrlField_0030`, `Dm_HrlField_0040`, `Dm_ZoraRiver_0005`) count as played. The Zora's River owl talk (advances the Zora quest) and the owls that fly Link (Lake Hylia, Death Mountain Trail) are kept. |
| `--skip-child-zelda` | **Experimental, not safe yet.** Starts with Zelda's Letter and Lullaby. Tested: completing the castle quest `Goto_HyruleCastle` at the start removes Mido and the early Kokiri; completing it on leaving the Deku Tree softlocks the forest-exit Kokiri. The quest also gates Lon Lon Ranch/Epona via Talon, and the `DoorOfTime` quest Zelda starts drives the Goron Ruby chain. |

How the skips work: a new file's starting values come from the save-data list (`GameData/GameDataList`, big-endian
BYML, names hashed with murmur3). Cutscenes have `HavePlayedEvent.<event>` flags; story progress is quests the game
calls Challenges, stored as enums named `Step_<Quest>` and advanced by events with `EventExecuteProgressChallengeStep`.
Items have `IsGet.<item>` and `PouchData.<item>.StockNum`.

Lift grades in the remake: None (Bombchus) < Low (bombs, bomb flowers, Goron Bracelet) < Middle (Silver Gauntlets) < High (Golden Gauntlets).

## How it works
- The remake runs on the *Tears of the Kingdom* engine. Each area's actors are in `Banc/<Area>/*.bcett.byml.zs`
  (BYML v7, zstd-compressed with the `bcett.byml.zsdic` dictionary).
- A chest's contents are its `Dynamic.Drop__DropActor` field (e.g. `Item_Sword_Kokiri`, `TBox_Rupee_Red`).
- **Move the item, leave the event behind.** Some chests have a `GetEventName` cutscene tied to the *place*
  (Kokiri Sword, Iron Boots -> Serenade of Water, Silver Gauntlets -> Nabooru). Moving the event with the item
  teleports Link into that cutscene; leaving it behind works fine (tested with the Kokiri Sword).
- Child and adult versions of an area are separate files, but a chest has the same `Hash` in both, so one location = one Hash.
- Files are rebuilt with `lib/bymlrw.py`, so any item can go in any area.
- **Size table** (`System/Resource/ResourceSizeTable...rsizetable.zs`): a scene file's entry is
  *size rounded up to 32, plus 264*. The randomizer grows entries when a file grows.
- **zstd headers must include the uncompressed size**, like Nintendo's files. Without it the game hangs on the boot loading screen.

## Tested in game
- Map/Slingshot chest swap (Deku Tree), Kokiri Sword in Mido's house: work.
- Junk shuffle seed 1109: works. Bombchus before a bomb bag show up with a count of 0, same as the N64 randomizer without a Bombchu setting.

## Where every kind of item lives
| Item source | Where it's defined | How hard to randomize |
|---|---|---|
| Chests | `Dynamic.Drop__DropActor` on `Obj_TBox_*` actors in scene files | **Done** |
| Business Scrubs | `Dynamic.ScrubBusiness_ShopItemActorName0/1/2` on `Enemy_Scrub_Business` actors; also referenced in `Enemy_Scrub_Business_*` events | Easy: same as chests, plus checking the scrub's talk event |
| Freestanding Heart Pieces | the actor itself is the item (`Gyaml: Obj_Heart_Piece`, no item field) | Medium: swap the actor type; untested whether the game keeps its "collected" state |
| NPC gifts, songs, minigame prizes, Great Fairies, trade items | item names inside event flows (`Event/EventFlow/*.bfevfl.zs`, Nintendo's BotW/TotK event format), e.g. `Npc_Zora_009` -> `Item_Scale_Silver`, `Dm_MelodyGet_Saria` -> `Item_Melody_SariaSong` | Medium-hard: needs an event flow reader/writer |
| Gold Skulltula tokens | built into `Enemy_Skulltula_Gold` (no item field); Skulltula House rewards are in the `GatheringTokenGold` event | Hard: needs code or actor replacement |
| Shops | the shelf actor is the item (`Shop_Heart`, `Shop_Bottle_Bug`, ...) | Medium: swap the actor type; prices are probably elsewhere |
| Boss heart containers | `Obj_Heart_Container` actors, also handed out in `Dm_*_BossOut` events | Easy for the actor, check the event |

The new `Item_ScrubBusinessSeed` collectible (chests and scrubs) has no N64 equivalent and will need its own logic.

## Logic
- `lib/logic.py`: locations with access rules, reachability, assumed fill (progression items are placed so the
  seed stays beatable; dungeon Map/Compass stay in their dungeon), and the playthrough by spheres.
- `logic/forest.py`: Kokiri Forest + Deku Tree rules, following OoTR.
- `logic/dodongo.py`: child Link to King Dodongo. Vanilla gifts (Fairy Ocarina, Zelda's Letter, songs, Goron Bracelet)
  are fixed events the logic follows but doesn't move. Chests whose requirements aren't confirmed are `junk_only`:
  they only swap junk, so a seed can't depend on them. Confirm one in game and it can become a normal location.
- `logic/forest_temple.py`: adds time travel (Ocarina of Time, Song of Time and the Master Sword as fixed events) and
  the Forest Temple (Hookshot to enter, Bow for most of it). Small keys and the Boss Key stay vanilla until key logic exists.
- `logic/jabu.py`: adds Zora's River/Domain and Jabu-Jabu; Ruto's Letter is the `Obj_Bottle_Letter` actor at the bottom
  of Lake Hylia (in `HyruleField_Child_Static`), reached with the Silver Scale from the Zora diving game. Mido checks the game's
  `IsGet.Weapon_Sword_Kokiri` and `IsGet.Weapon_Shield_Deku` flags, so a moved sword still gets Link past him.
- **Remake logic differences found in testing** (the N64 rules don't cover these):
  - Deku Tree 3rd floor (Compass room): the wall Skulltulas on the vine climb need the Slingshot.
  - Bombs need the Goron Bracelet: without it Link pulls a bomb out and puts it straight back.
    Any rule that uses bombs must require Bomb Bag **and** Goron Bracelet.
    Option `--bombs-without-bracelet` removes this (see Options).
- `logic/no_logic.py`: no logic, for trying the whole-game shuffle. 182 chests (generated from `tools/locations.py`'s CSV):
  small keys and boss keys stay vanilla, each Map/Compass stays in its dungeon, and only the Treasure Chest Shop's final
  heart-piece chest is used (the minigame picks the other chests' contents). Heart containers and freestanding items aren't chests.
- `lib/patch.py`: `ModBuilder` writes chest changes. Item-specific chest events (`ITEM_EVENTS`, e.g. the Kokiri Sword
  cutscene, Map/Compass/Boss Key, Navi tips about the item) are removed when the item leaves its chest; events that move
  the story or a quest on stay with the place (Nabooru taken away, Serenade of Water after the Iron Boots, the Ice Arrow
  quest, Ruto in Jabu-Jabu, Dampe's race, minigames). Many `GetEventName` values (e.g. `ForestTemple_GetBow`, the Map/Compass
  ones) don't exist in any event flow; removing them is harmless.

## Progressive items
`lib/logic.py` `PROGRESSIVE`: Hookshot -> Longshot, and Goron Bracelet -> Silver Gauntlets -> Gold Gauntlets. In the pool a
later tier is another copy of the first (rules use `state.has('Item_Hookshot',2)` for the Longshot). In the mod each copy is
a chest that gives the first tier Link doesn't have yet:
- The game's own substitute chest (`Obj_TBox_A_06`, vanilla for the Deku Shield chests that give rupees once you own a
  shield) gives `Drop__DropActor`, or `Drop__DropActor_Substitute` if Link owns `Drop__CheckActor` (pouch count, checked
  when the chest opens). Any small chest can switch to it (A_01 -> A_06, A_01_NoBake -> A_06_NoBake), so progressive
  copies only go in small chests. Tested: works on converted chests in any opening order; a lower tier still counts after an upgrade.
- Three tiers: `lib/progressive.py` adds nodes to the chest's AI graph (`AI/Obj_TBox_A_06.root.ainb` in both A_06
  packs): if Link already owns the substitute, it becomes the next tier from a fixed list (`NEXT_TIER`, e.g. Silver ->
  Gold Gauntlets). Tested in game. That check runs when the area loads (the substitute item is created then), while the
  first one runs when the chest opens, so two copies of a three-tier item never go in the same area.
- Adding chest settings instead (new instance params in the blackboard / `Drop_TreasureBox_A_06` param table) hangs the
  game on the loading screen, even with the actor's `InstanceHeapSize` (RSDB/ActorInfo) raised. Files inside packs
  have their own size table entries; the mod grows those too.
- Moving any item into a vanilla substitute chest clears its checks.

`lib/ainb.py` reads and writes AINB 0x408 (no attachments): all 1,936 loose AI/Logic/Sequence graphs round-trip
byte-identical, and still parse the same after every section is moved. It can add blackboard params, copy nodes and relink inputs.
`lib/sarc.py` `sarc_replace` rebuilds an archive with changed files (each file keeps its alignment).

## Event flows (NPC gifts, songs, shops)
`lib/evfl.py` reads all 914 `Event/EventFlow/*.bfevfl.zs` files (653 flowcharts, 261 cutscene timelines) and
`EvflWriter` changes parameter values. New strings are appended to the end of the string pool, so only the
relocation table behind it moves. Size table rule for event files: *size rounded up to 32, plus 272*.

Almost every gift is a call to a shared "get item" sub-routine with the item as a parameter, for example
`GetInEvent_*` (`ActorName`), `GetPouchContentByActorName` (medallions) and `NpcCommon_HandOver_NpcToPlayer_*`
(`ReveiveItem`, Nintendo's spelling). Changing that parameter changes the gift.

Business Scrubs: the scrub's `ScrubBusiness_ShopItemActorName0` field picks one of the options hardcoded in
`Enemy_Scrub_Business_Common` (Heart Piece / Deku Stick upgrade / Deku Nut upgrade), each with its own item, price
and sales text. Tested: a stick scrub set to `Obj_Heart_Piece` sold a Heart Piece for 100 rupees.

### Not located yet
- Goron Tunic and Zora Tunic (`Armor_Adult_Goron`, `Armor_Adult_Zora`): the NPC events only check for them, so the gift is set somewhere else, maybe in code.
- The Fire Arrows (`GetFireArrow` routine has no item parameter).
- Gold Skulltula tokens (built into the enemy).
