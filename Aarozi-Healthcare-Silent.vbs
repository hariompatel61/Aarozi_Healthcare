' Aarozi Healthcare — Silent Background Launcher
' Starts the clinical server without displaying a black command window

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strCurrentDir = fso.GetParentFolderName(WScript.ScriptFullName)

If fso.FileExists(strCurrentDir & "\AaroziHealthcareServer.exe") Then
    WshShell.Run """" & strCurrentDir & "\AaroziHealthcareServer.exe""", 0, False
ElseIf fso.FileExists(strCurrentDir & "\Aarozi-Healthcare-Launcher.bat") Then
    WshShell.Run """" & strCurrentDir & "\Aarozi-Healthcare-Launcher.bat""", 0, False
Else
    MsgBox "Aarozi Healthcare executable not found.", vbCritical, "Startup Error"
End If

