# Builds a logic seed: item placement, patched files, options, spoiler log and checks. Used by logic_seed.py and the GUI.
VERSION='0.1.1'
import os,random,importlib,collections
from .logic import assumed_fill,playthrough,progressive,PROGRESSIVE
from .patch import ModBuilder
from . import tweaks
from .checks import check_files,check_logic,check_events,gift_items

WORLDS={   # world module -> description shown to players
    'forest':'Kokiri Forest + Deku Tree (goal: Queen Gohma)',
    'dodongo':'Child Link to King Dodongo',
    'jabu':'All three child dungeons (goal: the three Spiritual Stones)',
    'forest_temple':'Through adult Link\'s first dungeon (goal: Phantom Ganon)',
    'no_logic':'No logic: every chest and some NPC gifts (may be unbeatable)',
}
OPTION_INFO={   # option -> (label, description, ready for players)
    'bombs_without_bracelet':('Bombs without Goron Bracelet','Bombs work without the bracelet.',True),
    'skip_opening':('Skip the opening','Every cutscene skippable; wake-up scenes count as done.',True),
    'skip_owls':('Skip owl cutscenes','Forced owl scenes in Hyrule Field and Zora\'s River count as played.',True),
    'skip_child_zelda':('Skip child Zelda (experimental)','Not safe yet: breaks story progress.',False),
}

def load_world(name,options):
    world=importlib.import_module('logic.'+name)
    for o in world.SETTINGS: world.SETTINGS[o]=o in options   # options the logic needs to know about
    return world

def seed_name(world,seed,options):
    name='Rando%s_%d'%(''.join(p.capitalize() for p in world.split('_')),seed)
    if options: name+='_'+''.join(w.capitalize() for o in options for w in o.split('_')[:2])
    return name

def build_seed(game,world_name,seed,options,out_dir=None,romfs_dir=None,spoiler_path=None,log=print):
    """Returns dict(name, mod, spoiler, problems). Either out_dir (mods/<title>/<name>/romfs + spoilers/ layout)
    or romfs_dir + spoiler_path."""
    options=[o for o in tweaks.OPTIONS if o in options]
    seed=seed if seed is not None else random.randrange(1,10**6)
    world=load_world(world_name,options); name=seed_name(world_name,seed,options)
    log('Reading game files...')
    mod=ModBuilder(game,out_dir,name,world.AREAS,romfs_dir=romfs_dir)
    log('Placing items (seed %d)...'%seed)
    locs=world.LOCATIONS; filler=[progressive(l.vanilla) for l in locs if not l.fixed]
    for p in world.PROGRESSION: filler.remove(p)
    pool=collections.Counter(filler+list(world.PROGRESSION))
    prog={b:PROGRESSIVE[b] for b in PROGRESSIVE if pool[b]>=2}   # progressive when the pool has more than one tier
    def spot_ok(item,l,placed):
        if item not in prog: return True
        if not mod.can_substitute(l.hash): return False   # small chests only
        # a three-tier chest picks its last tier when it loads, so copies can't share an area (see progressive.py)
        area=mod.chest_area(l.hash)
        return len(prog[item])<3 or not any(placed.get(o.name)==item and mod.chest_area(o.hash)==area for o in locs if o.hash)
    placed=assumed_fill(locs,world.PROGRESSION,filler,random.Random(seed),world.goal,world.RESTRICTED,spot_ok)
    for l in locs:
        if l.fixed: continue
        it=placed[l.name]
        if l.gift: mod.set_gift_item(l.gift,it)
        elif it in prog: mod.set_chest_item(l.hash,prog[it][0],upgrade=prog[it])
        else: mod.set_chest_item(l.hash,it)
    if options: log('Applying options: %s'%', '.join(options))
    tweaks.apply(mod,options)
    log('Writing mod files...'); path=mod.build()
    spoiler=spoiler_path or os.path.join(out_dir,'spoilers','spoiler_%s.txt'%name)
    os.makedirs(os.path.dirname(spoiler),exist_ok=True)
    with open(spoiler,'w') as f:
        f.write('%s - %s\n'%(name,world.__doc__.splitlines()[0]))
        f.write('Options: %s\n\nLocations:\n'%(', '.join(options) or 'none'))
        for l in locs:
            if l.fixed: continue
            it=placed[l.name]; shown=' then '.join(prog[it])+' (progressive)' if it in prog else it
            f.write('  %-46s %s%s%s\n'%(l.name,shown,'  (vanilla)' if it==progressive(l.vanilla) and it not in prog else '','  [junk only]' if l.junk_only else ''))
        if world.PROGRESSION:
            f.write('\nPlaythrough (progression items by sphere):\n')
            for i,sph in enumerate(playthrough(locs,placed,world.PROGRESSION)):
                if sph: f.write('  Sphere %d: %s\n'%(i+1,', '.join('%s -> %s'%x for x in sph)))
            f.write('  Then: the goal (%s)\n'%world.__doc__.split('Goal: ')[1].split('.')[0])
        else: f.write('\nNo logic: no playthrough. Keys stay in their vanilla chests.\n')
    log('Checking the result...')
    problems=[]; items,_=check_files(game,path,problems); check_events(game,path,problems)
    check_logic(world,items,problems,gift_items(game,path,world.LOCATIONS))
    return dict(name=name,seed=seed,mod=path,spoiler=spoiler,problems=problems)
