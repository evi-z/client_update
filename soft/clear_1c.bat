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

set qw1=3
set qw2=3
set qw3=3
set qw4=3
set qw5=3
set qw6=3

findstr "Srvr" %AppData%\1C\1CEStart\ibases.v8i&&set qw=1||set qw=0

rem echo %qw%

if %qw%==1 (
	findstr "pos-server" %AppData%\1C\1CEStart\ibases.v8i&&set qw1=0||set qw1=1
)

if %qw1%==0 (
rem "C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"pos-server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
rem	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"pos-server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"pos-server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"pos-server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
)
	
rem echo %qw1%

if %qw1%==1 (
	findstr "server" %AppData%\1C\1CEStart\ibases.v8i&&set qw2=0||set qw2=1
)

if %qw2%==0 (
rem	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
rem	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"server\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
)
	
rem echo %qw2%

if %qw2%==1 (
	findstr "kassa1" %AppData%\1C\1CEStart\ibases.v8i&&set qw3=0||set qw3=1
)

if %qw3%==0 (
rem	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa1\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
rem	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa1\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa1\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa1\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
)
	
rem echo %qw3%

if %qw3%==1 (
	findstr "kassa4" %AppData%\1C\1CEStart\ibases.v8i&&set qw4=0||set qw4=1
)

if %qw4%==0 (
rem	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa4\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
rem	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa4\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa4\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa4\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
)


rem echo %qw4%

if %qw4%==1 (
	findstr "kassa99" %AppData%\1C\1CEStart\ibases.v8i&&set qw5=0||set qw5=1
)

if %qw5%==0 (
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa99\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa99\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa99\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa99\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
)

rem echo %qw5%

if %qw5%==1 (
	findstr "kassa" %AppData%\1C\1CEStart\ibases.v8i&&set qw6=0||set qw6=1
)

if %qw6%==0 (
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ""
	"C:\Program Files\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
	"C:\Program Files (x86)\1cv8\common\1cestart.exe" ENTERPRISE /S"kassa\retail" /N"Администратор" /P""  /C РазрешитьРаботуПользователей /UC ПакетноеОбновлениеКонфигурацииИБ
)

	
rem echo %qw6%

rem pause