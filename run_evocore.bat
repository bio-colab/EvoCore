@echo off
chcp 65001 >nul
setlocal
title Darwin-Evolab EvoCore Launcher

set "QEMU_PATH=C:\Program Files\qemu\qemu-system-x86_64.exe"
set "BASE_DIR=%~dp0"
set "OUT_DIR=%BASE_DIR%output\minimal"
set "VMLINUZ=%OUT_DIR%\boot\vmlinuz"
set "CORE_GZ=%OUT_DIR%\boot\core.gz"
set "ISO_PATH=%OUT_DIR%\EvoCore-minimal.iso"

if not exist "%QEMU_PATH%" goto :no_qemu

echo =========================================================================
echo   DARWIN-EVOLAB -- EVOCORE v0.2.0 AUTONOMOUS SCIENTIFIC APPLIANCE
echo =========================================================================
echo.
echo اختر وضع التشغيل المرغوب / Select Operating Mode:
echo.
echo   [1] الوضع المعملي التفاعلي - Interactive Laboratory Mode [الافتراضي / Default]
echo       - نافذة مرئية تعرض تقدم التطور البيولوجي والفيزيائي وقوانين ستوكس-نيوتن
echo       - يبقى النظام قيد التشغيل بعد الانتهاء مع توفير سطر اوامر root
echo.
echo   [2] التشغيل المعملي الآلي الصامت - Headless Lab Runner + Evidence Export
echo       - يعمل في الخلفية دون واجهة مرئية، يكتشف القانون الرياضي
echo       - يحفظ وثيقة الإثبات المشفرة evidence_manifest.json على وندوز
echo       - ثم يطفئ الجهاز الافتراضي تلقائياً
echo.
echo   [3] وضع البحث التفاعلي - Research Shell Mode
echo       - إقلاع مباشر إلى سطر أوامر تفاعلي مع بيئة بايثون و Darwin-Evolab
echo.
echo   [4] إقلاع الـ ISO الكامل - Boot Full ISO via ISOLINUX Menu
echo       - محاكاة إقلاع حاسوب فعلي من القرص مع قائمة ISOLINUX
echo.
echo =========================================================================
set "CHOICE=1"
set /p "CHOICE=Enter choice [1-4] (Default 1): "

if "%CHOICE%"=="1" goto :mode1
if "%CHOICE%"=="2" goto :mode2
if "%CHOICE%"=="3" goto :mode3
if "%CHOICE%"=="4" goto :mode4
goto :mode1

:mode1
echo.
echo [*] Launching Interactive Laboratory GUI...
"%QEMU_PATH%" -kernel "%VMLINUZ%" -initrd "%CORE_GZ%" -append "console=tty0 quiet evomode=lab" -m 512M -name "Darwin-Evolab EvoCore [Lab Mode]"
goto :end

:mode2
echo.
echo [*] Starting Headless Scientific Discovery Runner...
echo [*] Running evolutionary search in memory and discovering physics laws...
"%QEMU_PATH%" -kernel "%VMLINUZ%" -initrd "%CORE_GZ%" -append "console=ttyS0 quiet evomode=lab evopoweroff=1" -serial file:"%BASE_DIR%output\last_run.log" -nographic -m 512M
echo.
echo [*] Experiment completed and VM powered off cleanly.
echo [*] Extracting signed evidence manifest...
python "%BASE_DIR%extract_manifest.py" "%BASE_DIR%output\last_run.log" "%BASE_DIR%output\evidence_manifest.json"
echo.
echo =========================================================================
echo [OK] Evidence manifest saved to:
echo      %BASE_DIR%output\evidence_manifest.json
echo =========================================================================
pause
goto :end

:mode3
echo.
echo [*] Launching Interactive Research Shell...
"%QEMU_PATH%" -kernel "%VMLINUZ%" -initrd "%CORE_GZ%" -append "console=tty0 quiet evomode=research" -m 512M -name "Darwin-Evolab EvoCore [Research Mode]"
goto :end

:mode4
echo.
echo [*] Booting Full ISO from Virtual CD-ROM...
"%QEMU_PATH%" -cdrom "%ISO_PATH%" -boot d -m 512M -name "Darwin-Evolab EvoCore [ISO Boot]"
goto :end

:no_qemu
echo =========================================================================
echo [!] لم يتم العثور على QEMU في المسار الافتراضي:
echo     %QEMU_PATH%
echo.
echo الرجاء تثبيت qemu-setup.exe الموجود في مجلد EvoCore اولاً.
echo =========================================================================
pause
exit /b 1

:end
