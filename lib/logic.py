# Logic core: locations with access rules, reachability, and an assumed-fill item placer.
import random

# Progressive items: a later tier counts as another copy of the first one (two 'Item_Hookshot' = Longshot), so rules
# write state.has('Item_Hookshot',2). In a chest, each copy gives the next tier Link doesn't have yet
# (see patch.ModBuilder.set_chest_item and progressive.py).
PROGRESSIVE={'Item_Hookshot':('Item_Hookshot','Item_Longshot'),
             'Item_Gauntlet_Goron':('Item_Gauntlet_Goron','Item_Gauntlet_Silver','Item_Gauntlet_Gold')}
_BASE={tier:base for base,tiers in PROGRESSIVE.items() for tier in tiers}
def progressive(item):
    """The pool name of an item: the first tier for a progressive item, otherwise the item itself."""
    return _BASE.get(item,item)

class Location:
    """A place that gives an item.
    fixed:     a vanilla gift we don't randomize (yet); it's an event the logic knows about, never patched.
    junk_only: a chest whose exact requirements aren't confirmed; it only swaps junk, so it can never
               hide something the seed needs."""
    def __init__(self,name,hash,vanilla,rule=lambda s:True,region='',fixed=False,junk_only=False):
        self.name=name; self.hash=hash; self.vanilla=vanilla; self.rule=rule; self.region=region
        self.fixed=fixed; self.junk_only=junk_only

class State:
    """The items Link has. Rules ask e.g. state.has('Item_Range_SlingShot')."""
    def __init__(self,items=()): self.items=list(items)
    def has(self,item,count=1): return self.items.count(item)>=count
    def copy(self): return State(self.items)

def reachable(locations,state,placed):
    """Collect everything reachable from `state`, picking up placed items as they become reachable.
    Returns (final state, reachable locations in the order they opened up)."""
    state=state.copy(); got=[]; seen=set(); changed=True
    while changed:
        changed=False
        for loc in locations:
            if loc.name not in seen and loc.rule(state):
                seen.add(loc.name); got.append(loc); changed=True
                if loc.name in placed: state.items.append(placed[loc.name])
    return state,got

def assumed_fill(locations,progression,filler,rng,goal,restricted=(),spot_ok=lambda item,loc,placed:True):
    """Place progression items so the seed stays beatable, then restricted items (e.g. a dungeon's Map,
    which must stay in its dungeon) in their allowed spots, then the rest at random.
    Assumed fill: each progression item goes to a spot reachable while assuming Link already
    has every progression item not placed yet. spot_ok(item, location, placed so far) can rule spots out for an item
    (e.g. progressive items only fit chests that can swap to the next tier)."""
    placed={l.name:l.vanilla for l in locations if l.fixed}
    open_spot=lambda l: l.name not in placed and not l.junk_only
    todo=list(progression); rng.shuffle(todo)
    while todo:
        item=todo.pop()
        st,reach=reachable(locations,State(todo),placed)
        spots=[l for l in reach if open_spot(l) and spot_ok(item,l,placed)]
        if not spots: raise RuntimeError('no reachable spot for '+item)
        placed[rng.choice(spots).name]=item
    filler=list(filler)
    for item,allowed in restricted:
        spots=[l for l in locations if open_spot(l) and allowed(l) and spot_ok(item,l,placed)]
        if not spots: raise RuntimeError('no allowed spot for '+item)
        placed[rng.choice(spots).name]=item; filler.remove(item)
    rest=[l for l in locations if l.name not in placed]
    if len(filler)!=len(rest): raise RuntimeError('item pool (%d) and empty locations (%d) differ'%(len(filler),len(rest)))
    rng.shuffle(filler); rng.shuffle(rest)
    picky=lambda item: not all(spot_ok(item,l,{}) for l in rest)
    for item in sorted(filler,key=lambda i: not picky(i)):   # items with fewer possible spots first
        spot=next((l for l in rest if spot_ok(item,l,placed)),None)
        if spot is None: raise RuntimeError('no spot left for '+item)
        placed[spot.name]=item; rest.remove(spot)
    final,_=reachable(locations,State(),placed)
    if not goal(final): raise RuntimeError('seed is not beatable')
    return placed

def playthrough(locations,placed,progression):
    """Spheres: what you can collect at each step, listing progression items and fixed (not shuffled) locations."""
    state=State(); spheres=[]; done=set(); fixed={l.name for l in locations if l.fixed}
    while True:
        _,reach=reachable(locations,state,{})
        new=[l for l in reach if l.name not in done]
        if not new: return spheres
        done|={l.name for l in new}
        for l in new: state.items.append(placed[l.name])
        spheres.append([(l.name+(' (vanilla)' if l.name in fixed else ''),placed[l.name]) for l in new
                        if placed[l.name] in progression or l.name in fixed])
