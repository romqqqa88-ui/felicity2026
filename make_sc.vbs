Set sys = CreateObject("WScript.Shell")
Set sc = sys.CreateShortcut("C:\Users\Romqqqa\Desktop\Felicity AI.lnk")
sc.TargetPath = "C:\Users\Romqqqa\.gemini\antigravity\scratch\felicity\kuni-master\FelicityLauncher.exe"
sc.WorkingDirectory = "C:\Users\Romqqqa\.gemini\antigravity\scratch\felicity\kuni-master"
sc.Save()
