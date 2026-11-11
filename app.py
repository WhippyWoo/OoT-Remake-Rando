"""OoT Remake Randomizer - desktop program. Shows the randomizer page in its own window (pywebview, which uses
the Edge WebView2 engine built into Windows). Packaged into OoT-Remake-Rando.exe by build_exe.ps1.

Usage:  python app.py      (needs: pip install pywebview)
"""
import webview
import gui
from lib.build import VERSION

def main():
    srv,url=gui.start_server()
    window=webview.create_window('OoT Remake Randomizer %s'%VERSION,url,width=960,height=920,min_size=(460,600))
    def pick_folder(title):
        result=window.create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None
    gui.FOLDER_PICKER=pick_folder
    gui.ON_QUIT=window.destroy
    webview.start()          # returns when the window is closed
    srv.shutdown()

if __name__=='__main__': main()
