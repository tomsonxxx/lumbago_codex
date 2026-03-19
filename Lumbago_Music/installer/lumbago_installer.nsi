; Lumbago Music AI — NSIS Installer Script
; Wymagania: NSIS 3.x

!define APP_NAME "Lumbago Music AI"
!define APP_VERSION "1.0.0"
!define APP_EXE "LumbagoMusic.exe"
!define INSTALL_DIR "$PROGRAMFILES64\LumbagoMusic"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "LumbagoMusic_Setup_${APP_VERSION}.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\LumbagoMusic" "InstallDir"
RequestExecutionLevel admin
Unicode True

; Sekcja instalacji
Section "Lumbago Music AI" SecMain
    SetOutPath "$INSTDIR"
    File /r "dist\LumbagoMusic\*"

    ; Skrót na pulpicie
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"

    ; Skrót w menu Start
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Odinstaluj.lnk" "$INSTDIR\Uninstall.exe"

    ; Rejestr
    WriteRegStr HKLM "Software\LumbagoMusic" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\LumbagoMusic" "Version" "${APP_VERSION}"

    ; Deinstalator
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LumbagoMusic" \
        "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LumbagoMusic" \
        "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LumbagoMusic" \
        "DisplayVersion" "${APP_VERSION}"
SectionEnd

; Sekcja deinstalacji
Section "Uninstall"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    DeleteRegKey HKLM "Software\LumbagoMusic"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LumbagoMusic"
SectionEnd
