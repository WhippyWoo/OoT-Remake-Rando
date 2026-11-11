"""Checks a built mod against the original game files.

- every changed scene file differs only in chest contents (and removed item-specific chest events)
- file headers carry the uncompressed size; size table entries cover the new files
- reading the chest contents back from the mod, the world's goal is reachable (logic replay),
  each dungeon's Map/Compass is in its dungeon, and no progression item sits in a junk-only chest

Usage:  python verify.py --mod RandoDodongo_N --world dodongo
"""
import argparse,os
from lib.game import Game,TITLE_ID,PROJECT,config
from lib.build import WORLDS,load_world
from lib.checks import check_files,check_logic

def main():
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dump',default=config().get('dump'))
    ap.add_argument('--mod',required=True); ap.add_argument('--world',required=True,choices=list(WORLDS))
    ap.add_argument('--out',default=os.path.join(PROJECT,'output')); args=ap.parse_args()
    name=args.mod; game=Game(args.dump); problems=[]
    mod=os.path.join(args.out,'mods',TITLE_ID,name,'romfs')
    items,nfiles=check_files(game,mod,problems)
    options=['bombs_without_bracelet'] if os.path.exists(os.path.join(mod,'Pack','Actor','Item_Bomb.pack.zs')) else []
    check_logic(load_world(args.world,options),items,problems)
    print('%s: %d scene files checked, %d problems'%(name,nfiles,len(problems)))
    for p in problems: print('  '+p)

if __name__=='__main__': main()
