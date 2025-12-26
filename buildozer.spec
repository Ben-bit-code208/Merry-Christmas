[app]

# Titel deiner App (wird auf dem Homescreen angezeigt)
title = Christmas Disco

# Name des Packages (muss eindeutig sein)
package.name = christmasdisco

# Domain für Package (umgekehrt)
package.domain = org.example

# Quellcode-Verzeichnis
source.dir = .

# Haupt-Python-Datei
source.include_exts = py,png,jpg,kv,atlas,mp3

# Version deiner App
version = 1.0

# Anforderungen (Bibliotheken)
requirements = python3,kivy,numpy,yt-dlp,requests,certifi,pycryptodome,websockets,mutagen,brotli,ffpyplayer

# Presplash-Hintergrundfarbe
#presplash.filename = %(source.dir)s/data/presplash.png

# Icon deiner App
#icon.filename = %(source.dir)s/data/icon.png

# Orientierung (landscape, portrait oder all)
orientation = portrait

# Android-spezifische Einstellungen

# Services (für Hintergrund-Tasks)
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

# Berechtigungen
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,WAKE_LOCK

# Android API Level
android.api = 31

# Minimum API Level
android.minapi = 21

# Android NDK Version
android.ndk = 25b

# Android SDK Version  
android.sdk = 31

# Accept Android SDK Lizenzen automatisch
android.accept_sdk_license = True

# Architektur (armeabi-v7a, arm64-v8a, x86, x86_64)
android.archs = arm64-v8a,armeabi-v7a

# Bootstrap (sdl2 für Kivy)
p4a.bootstrap = sdl2

# Zusätzliche Java-Klassen für Android
# android.add_jars = foo.jar,bar.jar,path/to/more/*.jar

# Zusätzliche AARs
# android.add_aars = project/libs/MYAarLib.aar

# Gradle-Dependencies
android.gradle_dependencies = com.android.support:support-v4:28.0.0

# Android-Whitelist (welche Dateien ins APK)
android.whitelist = lib-dynload/termios.so

# Python for Android (p4a) Directory
# p4a.source_dir = 

# Lokale Recipes (für custom builds)
# p4a.local_recipes = 

# URL für Bootstrap
# p4a.url = 

# Branch für Bootstrap
# p4a.branch = 

# Fork für p4a
# p4a.fork = 

# Port für buildozer
# p4a.port = 

[buildozer]

# Log level (0 = nur Fehler, 1 = normal, 2 = verbose)
log_level = 2

# Warnungen anzeigen
warn_on_root = 1

# Build-Verzeichnis
build_dir = ./.buildozer

# Binary-Verzeichnis  
bin_dir = ./bin