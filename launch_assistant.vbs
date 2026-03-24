Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectRoot = fso.GetParentFolderName(WScript.ScriptFullName)
pythonwPath = projectRoot & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonwPath) Then
    MsgBox "Не знайдено .venv\Scripts\pythonw.exe. Спочатку активуй або створи віртуальне середовище.", 16, "AI Assistant"
    WScript.Quit 1
End If

shell.CurrentDirectory = projectRoot
shell.Run Chr(34) & pythonwPath & Chr(34) & " -m ui.app", 0
