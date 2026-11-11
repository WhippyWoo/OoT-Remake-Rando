"""Seeds with logic. Each world in logic/ lists its locations, rules and goal:
  forest         Kokiri Forest + Deku Tree, goal Queen Gohma
  dodongo        child Link from Kokiri Forest to King Dodongo (gifts fixed, unconfirmed chests swap junk only)
  jabu           all three child dungeons, goal the three Spiritual Stones
  forest_temple  through to adult Link's first dungeon, goal Phantom Ganon
Progression items are always placed reachably; each dungeon's Map and Compass stay in that dungeon.
Every seed is checked after building (files and a logic replay).

Options (see lib/tweaks.py):
  --bombs-without-bracelet   bombs work without the Goron Bracelet (the remake normally requires it)
  --skip-opening             every cutscene skippable; wake-up scenes count as done
  --skip-owls                forced owl cutscenes in Hyrule Field and Zora's River count as played
  --skip-child-zelda         experimental, not safe yet

Usage:  python logic_seed.py --world dodongo [--seed N] [options] [--dump PATH] [--out PATH]
"""
import argparse,os
from lib.game import Game,PROJECT,config
from lib.build import build_seed,WORLDS
from lib import tweaks

def main():
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--world',required=True,choices=list(WORLDS))
    ap.add_argument('--dump',default=config().get('dump')); ap.add_argument('--seed',type=int,default=None)
    for o in tweaks.OPTIONS: ap.add_argument('--'+o.replace('_','-'),action='store_true')
    ap.add_argument('--out',default=os.path.join(PROJECT,'output')); args=ap.parse_args()
    r=build_seed(Game(args.dump),args.world,args.seed,[o for o in tweaks.OPTIONS if getattr(args,o)],out_dir=args.out)
    print('seed %d built\nmod:     %s\nspoiler: %s'%(r['seed'],r['mod'],r['spoiler'])); print(open(r['spoiler']).read())
    print('checks: %d problems'%len(r['problems'])); [print('  '+p) for p in r['problems']]

if __name__=='__main__': main()
