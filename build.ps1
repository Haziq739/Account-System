# Install Python dependencies if missing
Write-Host "Installing PyInstaller and Pillow..."
pip install pyinstaller pillow

# Convert PNG to ICO
Write-Host "Converting Logo to ICO..."
python -c "
from PIL import Image
from pathlib import Path
logo_path = Path('assets/k_dynamics_logo.png')
if logo_path.exists():
    img = Image.open(logo_path)
    img.save('assets/k_dynamics_logo.ico', format='ICO')
"

# Run PyInstaller
Write-Host "Building EXE with PyInstaller..."
pyinstaller --clean -y k_dynamics.spec

# Check for Inno Setup Compiler (ISCC)
$iscc = "$env:ProgramFiles (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    $iscc = "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $iscc)) {
    Write-Host "Inno Setup not found. Installing via winget..."
    winget install -e --id JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements --silent
    $iscc = "$env:ProgramFiles (x86)\Inno Setup 6\ISCC.exe"
}

if (Test-Path $iscc) {
    Write-Host "Building Installer with Inno Setup..."
    & $iscc build_installer.iss
    Write-Host "Build complete! Installer is located in the Output/ folder."
} else {
    Write-Error "Failed to locate Inno Setup after installation."
}
