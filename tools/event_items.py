"""Lists which event flows (cutscenes, NPC talks, minigames) mention which items, as a CSV.

This is a text scan, not a full event parser: a mention can be a gift, a check ("does Link have X?")
or a shown item. It shows where to look when a gift needs changing.

Usage:  python -m tools.event_items [--dump PATH] [--out FILE]
"""
import argparse,os,re,csv
from lib.game import Game,PROJECT,ZS_DICT,config,zread

ITEM=re.compile(rb'(?:Item_[A-Za-z0-9_]+|Obj_Heart_Piece|Obj_Heart_Container)(?=\0)')

def main():
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dump',default=config().get('dump'))
    ap.add_argument('--out',default=os.path.join(PROJECT,'output','event_items.csv')); args=ap.parse_args()
    game=Game(args.dump); rows=[]
    for rel in game.event_files():
        data=zread(game.path(rel),game.dict(ZS_DICT)); event=rel.split('/')[-1][:-len('.bfevfl.zs')]
        for item in sorted({m.group().decode() for m in ITEM.finditer(data)}):
            rows.append(dict(item=item,event=event))
    rows.sort(key=lambda r:(r['item'],r['event']))
    os.makedirs(os.path.dirname(args.out),exist_ok=True)
    with open(args.out,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['item','event']); w.writeheader(); w.writerows(rows)
    print('%d events scanned, %d item mentions, %d distinct items -> %s'%(len(game.event_files()),len(rows),len({r['item'] for r in rows}),args.out))

if __name__=='__main__': main()
