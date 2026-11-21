
# fix-venv.ps1
# Ensures Python 3.13.9 is installed (either standard or Conda), creates venv at C:\.NeaVenv, and activates it

# Step 1: Define expected Python paths
$pythonPathStandard = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe"
$pythonPathConda = "C:\Users\$env:USERNAME\anaconda3\envs\py3139\python.exe"

# Step 2: Function to check Python version
function Check-PythonVersion {
    param (
        [string]$path
    )
    if (Test-Path $path) {
        $versionOutput = & $path --version
        if ($versionOutput -like "Python 3.13.9*") {
            Write-Host "Found Python 3.13.9 at $path"
            return $true
        } else {
            Write-Host "Python found at $path, but version is $versionOutput (expected 3.13.9)."
        }
    }
    return $false
}

# Step 3: Verify Python 3.13.9 exists in either location
$pythonPath = $null
if (Check-PythonVersion -path $pythonPathStandard) {
    $pythonPath = $pythonPathStandard
} elseif (Check-PythonVersion -path $pythonPathConda) {
    $pythonPath = $pythonPathConda
} else {
    Write-Host "Python 3.13.9 not found in standard or Conda paths."
    Write-Host "Please install Python 3.13.9 from https://www.python.org/downloads/windows/ or create Conda env."
    exit
}

# Step 4: Create venv at C:\.NeaVenv if missing
$venvPath = "C:\.NeaVenv"
if (-Not (Test-Path $venvPath)) {
    & $pythonPath -m venv $venvPath
    Write-Host "Created new venv at $venvPath"
} else {
    Write-Host "Found existing venv at $venvPath"
}

# Step 5: Activate venv
$activateScript = "C:\.NeaVenv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "Activated venv at $venvPath"
} else {
    Write-Host "Activation script not found at $activateScript"
}
