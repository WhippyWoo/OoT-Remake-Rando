# Three-tier progressive chests (e.g. Goron Bracelet -> Silver Gauntlets -> Gold Gauntlets).
# The game's substitute chest (Obj_TBox_A_06) gives Drop__DropActor, or Drop__DropActor_Substitute if Link owns
# Drop__CheckActor (one check, two tiers; its AI graph decides). This adds a second check to that graph: if Link
# already owns the substitute, it becomes the next tier from a fixed list (Silver Gauntlets -> Gold Gauntlets...).
# The chest's blackboard and parameter table stay as they are: adding parameters there hangs the game on the
# loading screen (tested), so the third tier comes from the list instead of a new chest setting.
# The substitute's item is created when the chest loads, so the second check is made then, while the first one is
# made when the chest opens: two copies of a three-tier item must not share an area (see build.py).
from .ainb import Ainb
from .sarc import sarc_files,sarc_replace
from .game import zread
from .logic import PROGRESSIVE

PACKS=('Pack/Actor/Obj_TBox_A_06.pack.zs','Pack/Actor/Obj_TBox_A_06_NoBake.pack.zs')
GRAPH='AI/Obj_TBox_A_06.root.ainb'
STRING,INT,BOOL=3,0,1   # node parameter types
NEXT_TIER={tiers[1]:tiers[2] for tiers in PROGRESSIVE.values() if len(tiers)==3}

def _node(a,name,test=lambda i:True):
    hits=[i for i,n in enumerate(a.nodes) if a.str_at(n.name_off)==name and test(i)]
    if len(hits)!=1: raise ValueError('expected one %s node, found %d'%(name,len(hits)))
    return hits[0]

def patch_graph(data,next_tier=NEXT_TIER):
    a=Ainb(data); sub=a.blackboard_params(0).index('Drop__DropActor_Substitute')
    reads_sub=lambda i,name: (lambda j:a.inputs[STRING][j][8:12]==(0x80000000|sub).to_bytes(4,'little'))(a._input(i,STRING,name))
    pouch=_node(a,'QueryGetPouchContentNumByActorName'); less=_node(a,'QueryMathLessS32')
    first=lambda name: [i for i,n in enumerate(a.nodes) if a.str_at(n.name_off)==name][0]   # a template to copy
    equal=first('QueryStringIsEqual'); select=first('QuerySelectStringByBool')
    holder=_node(a,'OneShotActorHolderTryRequestCreateActorWithActorFileName',lambda i:reads_sub(i,'ActorFileName'))
    sub_name=_node(a,'QuerySelectStringByBool',lambda i:reads_sub(i,'B'))
    def mark_used(i):   # the select's output is read by another node
        b,_=a.nodes[i].outputs[STRING]; e=bytearray(a.outputs[STRING][b]); e[3]|=0x80; a.outputs[STRING][b]=bytes(e)
    # next tier of the substitute: a chain of "substitute == X ? Y : (previous)", starting from the substitute itself
    nxt=None
    for t2,t3 in sorted(next_tier.items()):
        is_t2=a.add_node(equal); a.input_from_blackboard(is_t2,STRING,'StringA',sub); a.input_constant(is_t2,STRING,'StringB',t2)
        pick=a.add_node(select); a.link_input(pick,BOOL,'Bool',is_t2); a.input_constant(pick,STRING,'A',t3)
        if nxt is None: a.input_from_blackboard(pick,STRING,'B',sub); a.set_node_queries(pick,[is_t2])
        else: a.link_input(pick,STRING,'B',nxt); a.set_node_queries(pick,[is_t2,nxt])
        mark_used(pick); nxt=pick
    has=a.add_node(pouch); a.input_from_blackboard(has,STRING,'ActorName',sub)           # how many substitutes Link owns
    more=a.add_node(less); a.link_input(more,INT,'S32Base',has); a.set_node_queries(more,[has])   # 0 < that
    final=a.add_node(select); a.link_input(final,BOOL,'Bool',more); a.link_input(final,STRING,'A',nxt)
    a.input_from_blackboard(final,STRING,'B',sub); a.set_node_queries(final,[more,nxt]); mark_used(final)
    for i,name in ((holder,'ActorFileName'),(sub_name,'B')):   # the substitute item and its name now come from here
        a.link_input(i,STRING,name,final); a.set_node_queries(i,a.node_queries(i)+[final])
    return a.build()

def three_tier_chests(mod):
    """Add the patched substitute chests to the mod."""
    g=mod.game; d=g.dict('pack.zsdic')
    for rel in PACKS:
        raw=zread(g.path(rel),d); files=sarc_files(raw); changes={GRAPH:patch_graph(files[GRAPH])}
        for name,data in changes.items(): mod.grow_entry(name,len(files[name]),len(data))   # files in a pack have their own entries
        mod.add_file(rel,sarc_replace(raw,changes),d,len(raw))
