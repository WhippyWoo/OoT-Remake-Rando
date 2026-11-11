"""Builds a mod with only gameplay tweaks (no randomization), e.g. to try them on a normal playthrough.

Usage:  python tweaks_mod.py --skip-opening --skip-owls [--bombs-without-bracelet] [--skip-child-zelda] [--name NAME]
"""
import argparse,os
from lib.game import Game,PROJECT,config
from lib.patch import ModBuilder
from lib import tweaks

ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument('--dump',default=config().get('dump')); ap.add_argument('--out',default=os.path.join(PROJECT,'output'))
ap.add_argument('--name',default='Tweaks')
for o in tweaks.OPTIONS: ap.add_argument('--'+o.replace('_','-'),action='store_true')
args=ap.parse_args(); options=[o for o in tweaks.OPTIONS if getattr(args,o)]
if not options: raise SystemExit('choose at least one option')
mod=ModBuilder(Game(args.dump),args.out,args.name,areas=())
changes=tweaks.apply(mod,options); path=mod.build()
print('options:',', '.join(options)); print('%d save-data changes'%len(changes)); print('mod:',path)
