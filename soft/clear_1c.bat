@echo off

If Exist %APPDATA%\1C\1cv8 (
@echo Очистка Roaming
for /d %%i in ("%APPDATA%\1C\1Cv8\????????-????-????-????-????????????") do (
rmdir /s /q "%%i"
@echo "%%i"))

If Exist %localappdata%\1c\1Cv8 (
@echo Удаляем все каталоги v8
for /d %%i in ("%localappdata%\1c\1Cv8\*") do (
rmdir /s /q "%%i"
@echo "%%i"))

If Exist %APPDATA%\1C\1cv82 (
@echo Очистка Roaming
for /d %%i in ("%APPDATA%\1C\1Cv82\????????-????-????-????-????????????") do (
rmdir /s /q "%%i"
@echo "%%i"))

If Exist %localappdata%\1c\1Cv82 (
@echo Удаляем все каталоги v82
for /d %%i in ("%localappdata%\1c\1Cv82\*") do (
rmdir /s /q "%%i"
@echo "%%i"))

@echo Чистим temp
if not defined temp exit/b
cd /d "%temp%" || exit/b
if /i not "%temp%" == "%cd%" exit/b
rd /s /q "%temp%" >nul 2>&1

Del C:\retail\*.cdn

"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"server/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"server/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa4/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa4/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa99/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa99/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa1/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa1/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"pos-server/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения
"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"pos-server/retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UCКодРазрешения

