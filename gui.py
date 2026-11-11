"""OoT Remake Randomizer - the page and its server. The desktop program (app.py) shows it in its own window;
running this file directly shows it in your browser instead. The server only listens on this PC (127.0.0.1).

Usage:  python gui.py [--port N] [--no-browser]
"""
import argparse,json,os,platform,random,secrets,subprocess,sys,threading,traceback,webbrowser
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from lib import zst
from lib.game import Game,PROJECT,RESOURCES,TITLE_ID,SUPPORTED_VERSION,find_romfs,check_romfs
from lib.build import build_seed,seed_name,WORLDS,OPTION_INFO,VERSION
from lib.tweaks import OPTIONS

SETTINGS=os.path.join(PROJECT,'settings.json')
TOKEN=secrets.token_hex(16)
JOB={'running':False,'log':[],'result':None,'error':None}
LOCK=threading.Lock()
FOLDER_PICKER=None   # set by app.py to use the window's native folder dialog
ON_QUIT=None         # set by app.py to close the window

DEFAULTS={'out':os.path.join(PROJECT,'seeds'),'world':'forest_temple','options':['skip_opening','skip_owls']}
def load_settings():
    try: s=json.load(open(SETTINGS))
    except Exception: s={}
    return {**DEFAULTS,**{k:v for k,v in s.items() if v}}
def save_settings(s):
    try: json.dump(s,open(SETTINGS,'w'),indent=1)
    except OSError: pass

def browse_folder(title):
    """Native folder picker: the app window's dialog, else PowerShell on Windows, osascript on macOS,
    zenity/kdialog on Linux, else tkinter."""
    if FOLDER_PICKER: return FOLDER_PICKER(title)
    try:
        if os.name=='nt':
            ps=("Add-Type -AssemblyName System.Windows.Forms;$d=New-Object System.Windows.Forms.FolderBrowserDialog;"
                "$d.Description='%s';$d.ShowNewFolderButton=$true;if($d.ShowDialog() -eq 'OK'){$d.SelectedPath}"%title.replace("'",""))
            r=subprocess.run(['powershell','-NoProfile','-STA','-Command',ps],capture_output=True,text=True,timeout=600)
            return r.stdout.strip() or None
        if sys.platform=='darwin':
            r=subprocess.run(['osascript','-e','POSIX path of (choose folder with prompt "%s")'%title],capture_output=True,text=True,timeout=600)
            return r.stdout.strip() or None
        for cmd in (['zenity','--file-selection','--directory','--title',title],['kdialog','--getexistingdirectory','.']):
            try:
                r=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
                return r.stdout.strip() or None
            except FileNotFoundError: continue
        import tkinter,tkinter.filedialog
        root=tkinter.Tk(); root.withdraw(); p=tkinter.filedialog.askdirectory(title=title); root.destroy(); return p or None
    except Exception:
        return None

def open_path(path):
    if os.name=='nt': os.startfile(path)
    elif sys.platform=='darwin': subprocess.Popen(['open',path])
    else: subprocess.Popen(['xdg-open',path])

def run_job(req):
    def log(msg):
        with LOCK: JOB['log'].append(msg)
    try:
        game=Game(base=req['base'],update=req['update'])
        text=str(req.get('seed') or '').strip()
        seed=int(text) if text else random.randrange(1,10**6)      # the folder name needs the seed up front
        options=[o for o in OPTIONS if o in req.get('options',[]) and OPTION_INFO[o][2]]   # standard order; only options ready for players
        name=seed_name(req['world'],seed,options); folder=os.path.join(req['out'],name)
        r=build_seed(game,req['world'],seed,options,romfs_dir=os.path.join(folder,'romfs'),
                     spoiler_path=os.path.join(folder,'spoiler.txt'),log=log)
        r['folder']=folder; r['world']=req['world']; r['options']=options
        log('Done: %s (%d problems found by the checks)'%(name,len(r['problems'])))
        with LOCK: JOB['result']=r
    except Exception as ex:
        with LOCK: JOB['error']='%s: %s'%(type(ex).__name__,ex); JOB['log'].append(traceback.format_exc())
    finally:
        with LOCK: JOB['running']=False

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _send(self,code,body,ctype='application/json'):
        data=body if isinstance(body,bytes) else json.dumps(body).encode()
        self.send_response(code); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path in ('/','/index.html'):
            html=open(os.path.join(RESOURCES,'web','index.html'),encoding='utf-8').read().replace('__TOKEN__',TOKEN)
            return self._send(200,html.encode(),'text/html; charset=utf-8')
        if self.headers.get('X-Token')!=TOKEN: return self._send(403,{'error':'forbidden'})
        if self.path=='/api/info':
            return self._send(200,dict(version=VERSION,game_version=SUPPORTED_VERSION,title_id=TITLE_ID,backend=zst.BACKEND,
                os=platform.system(),worlds=WORLDS,options=[dict(id=o,label=OPTION_INFO[o][0],desc=OPTION_INFO[o][1],ready=OPTION_INFO[o][2]) for o in OPTIONS],
                settings=load_settings()))
        if self.path=='/api/job':
            with LOCK: return self._send(200,dict(JOB))
        self._send(404,{'error':'not found'})
    def do_POST(self):
        if self.headers.get('X-Token')!=TOKEN: return self._send(403,{'error':'forbidden'})
        req=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
        if self.path=='/api/check':
            base,update=req.get('base'),req.get('update')
            if req.get('dump'): base,update=find_romfs(req['dump'])
            return self._send(200,dict(base=base,update=update,problems=check_romfs(base,update)))
        if self.path=='/api/browse':
            return self._send(200,dict(path=browse_folder(req.get('title','Choose a folder'))))
        if self.path=='/api/open':
            p=req.get('path','')
            if os.path.exists(p): open_path(p); return self._send(200,{'ok':True})
            return self._send(404,{'error':'path not found'})
        if self.path=='/api/generate':
            problems=check_romfs(req.get('base'),req.get('update'))
            if problems: return self._send(400,{'error':' '.join(problems)})
            if req.get('world') not in WORLDS: return self._send(400,{'error':'unknown world'})
            with LOCK:
                if JOB['running']: return self._send(409,{'error':'already generating'})
                JOB.update(running=True,log=[],result=None,error=None)
            save_settings({**{k:req.get(k) for k in ('dump','base','update','out','world')},
                           'options':[o for o in req.get('options',[]) if OPTION_INFO.get(o,('','',False))[2]]})
            threading.Thread(target=run_job,args=(req,),daemon=True).start()
            return self._send(200,{'ok':True})
        if self.path=='/api/quit':
            self._send(200,{'ok':True})
            threading.Thread(target=ON_QUIT or self.server.shutdown,daemon=True).start(); return
        self._send(404,{'error':'not found'})

def start_server(port=0):
    """Starts the server in a background thread; returns (server, url)."""
    srv=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=srv.serve_forever,daemon=True).start()
    return srv,'http://127.0.0.1:%d/'%srv.server_address[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--port',type=int,default=0); ap.add_argument('--no-browser',action='store_true'); args=ap.parse_args()
    srv,url=start_server(args.port); done=threading.Event()
    global ON_QUIT
    ON_QUIT=lambda: (srv.shutdown(),done.set())
    print('OoT Remake Randomizer %s running at %s'%(VERSION,url)); print('Keep this window open while using it. Quit from the page or press Ctrl+C.')
    if not args.no_browser: webbrowser.open(url)
    try: done.wait()
    except KeyboardInterrupt: srv.shutdown()
    print('Stopped.')

if __name__=='__main__': main()
