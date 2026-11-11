"""Lists every chest and heart container in the game as a CSV (child/adult copies merged).

Usage:  python -m tools.locations [--dump PATH] [--out FILE]
"""
import argparse,os,csv,struct
from lib.game import Game,PROJECT,config,actor_hash,area_of

def main():
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dump',default=config().get('dump'))
    ap.add_argument('--out',default=os.path.join(PROJECT,'output','oot_remake_locations.csv')); args=ap.parse_args()
    game=Game(args.dump); locs={}
    for rel in game.scene_files():
        if area_of(rel)=='DreamWorld': continue
        _,root=game.read_scene(rel); name=rel.split('/')[-1].replace('.bcett.byml.zs','')
        for a in root.get('Actors',[]):
            g=a.get('Gyaml',''); dyn=a.get('Dynamic') or {}; item=dyn.get('Drop__DropActor')
            if not ('TBox' in g and item is not None or 'Heart_Container' in g or g.startswith('Item_')): continue
            h=actor_hash(a)
            if h in locs: locs[h]['files']+=' + '+name; continue
            pos=' '.join('%.1f'%struct.unpack('<f',struct.pack('<I',c.v))[0] for c in a.get('Translate',[]))
            event=dyn.get('GetEventName','')
            kind='freestanding item' if g.startswith('Item_') else 'heart container' if 'Heart_Container' in g else 'shop minigame chest' if 'Shop' in g else 'big chest' if '_A_02' in g else 'chest'
            note='new remake collectible' if item=='Item_ScrubBusinessSeed' else ''
            if event and not event.endswith('NaviChatOff'): note=(note+'; ' if note else '')+'special event - keep with location'
            locs[h]=dict(area=area_of(rel),kind=kind,item=item or '',event=event,room=dyn.get('DefaultDungeonRoomIndex',''),actor=g,hash=h,pos=pos,files=name,note=note)
    rows=sorted(locs.values(),key=lambda x:(x['area'],x['kind']!='big chest',str(x['room'])))
    for r in rows: r['age']='both' if 'Child' in r['files'] and 'Adult' in r['files'] else 'child' if 'Child' in r['files'] else 'adult' if 'Adult' in r['files'] else 'dungeon'
    os.makedirs(os.path.dirname(args.out),exist_ok=True)
    with open(args.out,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['area','age','kind','item','event','room','actor','hash','pos','files','note']); w.writeheader(); w.writerows(rows)
    print(len(rows),'locations ->',args.out)

if __name__=='__main__': main()
