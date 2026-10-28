# run_evocore.ps1 — PowerShell Multi-Mode Launcher for EvoCore
$Host.UI.RawUI.WindowTitle = "Darwin-Evolab EvoCore Launcher"
$qemuPath = "C:\Program Files\qemu\qemu-system-x86_64.exe"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outDir = Join-Path $scriptDir "output\minimal"
$vmlinuz = Join-Path $outDir "boot\vmlinuz"
$coreGz = Join-Path $outDir "boot\core.gz"
$isoPath = Join-Path $outDir "EvoCore-minimal.iso"
$lastRunLog = Join-Path $scriptDir "output\last_run.log"
$manifestOut = Join-Path $scriptDir "output\evidence_manifest.json"

if (-not (Test-Path $qemuPath)) {
    Write-Host "=========================================================================" -ForegroundColor Red
    Write-Host "[!] لم يتم العثور على QEMU في المسار الافتراضي:" -ForegroundColor Yellow
    Write-Host "    $qemuPath"
    Write-Host ""
    Write-Host "الرجاء تثبيت qemu-setup.exe الموجود في مجلد EvoCore أولاً." -ForegroundColor Cyan
    Write-Host "=========================================================================" -ForegroundColor Red
    Read-Host "اضغط Enter للمتابعة..."
    exit 1
}

Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "  DARWIN-EVOLAB -- EVOCORE v0.3.0 AUTONOMOUS SCIENTIFIC APPLIANCE" -ForegroundColor Green
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "اختر وضع التشغيل المرغوب:" -ForegroundColor White
Write-Host ""
Write-Host "  [1] الوضع المعملي التفاعلي (Interactive Laboratory Mode) [الافتراضي]" -ForegroundColor Yellow
Write-Host "      - نافذة مرئية تعرض تقدم التطور البيولوجي والفيزيائي وقوانين ستوكس-نيوتن"
Write-Host "      - يبقى النظام قيد التشغيل بعد الانتهاء مع توفير سطر أوامر root"
Write-Host ""
Write-Host "  [2] التشغيل المعملي الصامت + كبسولة الإثبات المشفرة (.evobundle)" -ForegroundColor Yellow
Write-Host "      - يعمل في الخلفية دون واجهة مرئية، يكتشف القانون الرياضي"
Write-Host "      - ينشئ وثيقة الإثبات المشفرة evidence_manifest.json وحزمة .evobundle"
Write-Host "      - ثم يطفئ الجهاز الافتراضي تلقائياً"
Write-Host ""
Write-Host "  [3] وضع البحث التفاعلي (Research Shell Mode)" -ForegroundColor Yellow
Write-Host "      - إقلاع مباشر إلى سطر أوامر تفاعلي مع بيئة بايثون و Darwin-Evolab"
Write-Host ""
Write-Host "  [4] إقلاع الـ ISO الكامل (Boot Full ISO via ISOLINUX Menu)" -ForegroundColor Yellow
Write-Host "      - محاكاة إقلاع حاسوب فعلي من القرص مع قائمة ISOLINUX"
Write-Host ""
Write-Host "  [5] سطر أوامر EvoCore التفاعلي (Interactive REPL Shell)" -ForegroundColor Yellow
Write-Host "      - بيئة إدارة وتدقيق فورية مع إكمال تلقائي للأوامر"
Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan

$choice = Read-Host "أدخل رقم الخيار [1-5] واضغط Enter (الافتراضي 1)"
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }
$choice = $choice.Trim()

switch ($choice) {
    "1" {
        Write-Host "`n[*] جاري تشغيل الوضع المعملي التفاعلي (Laboratory GUI)..." -ForegroundColor Green
        python -m evocore.cli run --mode lab --gui
    }
    "2" {
        Write-Host "`n[*] جاري تشغيل وضع الاستكشاف العلمي الآلي الصامت وحزم الأدلة..." -ForegroundColor Cyan
        python -m evocore.cli run --mode lab --headless --bundle
        Read-Host "`nاضغط Enter للمتابعة..."
    }
    "3" {
        Write-Host "`n[*] جاري تشغيل وضع البحث التفاعلي (Research Shell)..." -ForegroundColor Green
        python -m evocore.cli run --mode research --gui
    }
    "4" {
        Write-Host "`n[*] جاري إقلاع الـ ISO الكامل عبر محاكي مشغل الأقراص..." -ForegroundColor Green
        python -m evocore.cli run --mode iso --gui
    }
    "5" {
        Write-Host "`n[*] جاري تشغيل سطر أوامر EvoCore التفاعلي..." -ForegroundColor Green
        python -m evocore.cli repl
    }
    default {
        Write-Host "[!] خيار غير صالح." -ForegroundColor Red
    }
}
