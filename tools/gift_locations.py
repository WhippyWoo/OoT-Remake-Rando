"""Lists every item given by an event (NPC gifts, songs, medallions, Great Fairies, minigames, shops) as a CSV.

One location = one event + the item it hands out. Events with a ".110" copy (patched in update 1.1.0)
are merged with it: both files must be changed together. 'steps' lists every event step whose parameter
names that item and must change together when the gift is randomized (e.g. the get-item animation and
the step that adds the item to the inventory).

Usage:  python -m tools.gift_locations [--dump PATH] [--out FILE]
"""
import argparse,os,re,csv,collections
from lib.game import Game,PROJECT,ZS_DICT,config,zread
from lib.evfl import Evfl

ITEM=re.compile(r'^(Item_|Obj_Heart_Piece$|Obj_Heart_Container$)')
# shared sub-routines that hand an item to Link, and which parameter names the item
GIFT_PARAMS={'ActorName','ReveiveItem','ReceiveItem','TakenRewardActor','DropActorName'}
# events that aren't item locations: system/debug grants and the Boss Rush (DreamWorld) mode
SKIP_EVENTS={'Dm_SY_Ocarina','Enemy_Scrub_Business_Dream','SubEvent_AllBossBattle'}

def is_gift_routine(name):
    return name.startswith(('GetInEvent','GetPouchContent','NpcCommon_HandOver_NpcToPlayer','DisplayGetByActorName',
        'DisplayRutoGetByActorName','TakenReward_Common_Event','GetItemSword','MushiToriGame','DiggingHoleTour_Demo',
        'SimpleShopSub_Scrub_Business_OneTime','GetBottle_Animation','GetDisplayProcess'))

def gift_steps(e):
    """(step index, step kind, routine/action name, parameter, item) for every gift step in an event file."""
    out=[]
    for ev in e.events:
        if ev['kind']=='subflow':
            name,p=e.subflow(ev)
            if is_gift_routine(name):
                for k,v in (p or {}).items():
                    if k in GIFT_PARAMS and isinstance(v,str) and ITEM.match(v): out.append((ev['idx'],'subflow',name,k,v))
        elif ev['kind']=='action':
            a=e.actors[ev['actor']]; act=a['actions'][ev['action']]; p=ev['params'] or {}
            if act=='EventTriggerAddOrRemovePouchContent' and isinstance(p.get('Num'),int) and p['Num']>0 and ITEM.match(str(p.get('Actor',''))):
                out.append((ev['idx'],'action',a['name']+'.'+act,'Actor',p['Actor']))
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dump',default=config().get('dump'))
    ap.add_argument('--out',default=os.path.join(PROJECT,'output','gift_locations.csv')); args=ap.parse_args()
    game=Game(args.dump); groups=collections.defaultdict(lambda:dict(files=set(),steps=[]))
    for rel in game.event_files():
        file=rel.split('/')[-1][:-len('.bfevfl.zs')]; event=file.split('.')[0]
        if event in SKIP_EVENTS: continue
        e=Evfl(zread(game.path(rel),game.dict(ZS_DICT)))
        for idx,kind,routine,param,item in gift_steps(e):
            gr=groups[(event,item)]; gr['files'].add(file); gr['steps'].append('%s#%d:%s:%s'%(file,idx,routine,param))
    rows=[dict(event=ev,item=it,files=' + '.join(sorted(g['files'])),steps=' | '.join(g['steps'])) for (ev,it),g in groups.items()]
    rows.sort(key=lambda r:(r['event'],r['item']))
    os.makedirs(os.path.dirname(args.out),exist_ok=True)
    with open(args.out,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['event','item','files','steps']); w.writeheader(); w.writerows(rows)
    print('%d gift locations in %d events -> %s'%(len(rows),len({r['event'] for r in rows}),args.out))

if __name__=='__main__': main()
