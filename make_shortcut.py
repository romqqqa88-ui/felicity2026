import os

desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
shortcut_path = os.path.join(desktop, 'Felicity AI.lnk')
target = r'C:\Users\Romqqqa\.gemini\antigravity\scratch\felicity\kuni-master\FelicityLauncher.exe'
workdir = r'C:\Users\Romqqqa\.gemini\antigravity\scratch\felicity\kuni-master'

vbs_content = f'''Set sys = CreateObject("WScript.Shell")
Set sc = sys.CreateShortcut("{shortcut_path}")
sc.TargetPath = "{target}"
sc.WorkingDirectory = "{workdir}"
sc.Save()
'''

with open('make_sc.vbs', 'w', encoding='utf-8') as f:
    f.write(vbs_content)

os.system('cscript //nologo make_sc.vbs')
print("Desktop shortcut created!")
