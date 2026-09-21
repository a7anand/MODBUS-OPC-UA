' Run gateway with no console window (background + Web UI only).
Set sh = CreateObject("WScript.Shell")
exe = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\ModbusOPCUAGateway.exe"
sh.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.Run """" & exe & """ --headless --config config\gateway.yaml", 0, False
