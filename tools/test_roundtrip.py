"""Sanity test for the BYML writer: rebuild every unmodified scene file and compare with the original.
Every file should come back with identical data and identical size.

Usage:  python -m tools.test_roundtrip [--dump PATH]
"""
import argparse
from lib.game import Game,BCETT_DICT,config,zread
from lib.bymlrw import read,write

ap=argparse.ArgumentParser(); ap.add_argument('--dump',default=config().get('dump')); args=ap.parse_args()
game=Game(args.dump); bad=0; files=game.scene_files()
for rel in files:
    raw=zread(game.path(rel),game.dict(BCETT_DICT)); ver,a=read(raw); out=write(a,ver)
    if read(out)[1]!=a or len(out)!=len(raw): bad+=1; print('MISMATCH',rel)
print('%d files, %d mismatches'%(len(files),bad))
