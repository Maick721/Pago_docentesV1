[CmdletBinding()]
param(
    [string]$PythonVersion = "3.13",
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$pythonEnvironment = Join-Path $repositoryRoot ".venv"
$pythonExecutable = Join-Path $pythonEnvironment "Scripts\python.exe"

function Invoke-CheckedCommand {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "El comando '$Command $($Arguments -join ' ')' terminó con código $LASTEXITCODE."
    }
}

function Copy-ExampleIfMissing {
    param(
        [string]$ExamplePath,
        [string]$TargetPath
    )

    if (-not (Test-Path $TargetPath)) {
        Copy-Item $ExamplePath $TargetPath
        Write-Host "Creado: $TargetPath"
    }
    else {
        Write-Host "Conservado: $TargetPath"
    }
}

Push-Location $repositoryRoot
try {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw "No se encontró el launcher 'py'. Instala Python $PythonVersion y vuelve a ejecutar."
    }
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        throw "No se encontró npm. Instala Node.js 24 LTS y vuelve a ejecutar."
    }

    Invoke-CheckedCommand "py" @("-$PythonVersion", "--version")
    Copy-ExampleIfMissing ".env.example" ".env"
    Copy-ExampleIfMissing "backend\.env.example" "backend\.env"

    $backendEnvironment = Get-Content "backend\.env" -Raw
    if ($backendEnvironment -match "(?m)^SECRET_KEY=(replace_with_a_secure_random_value)?\s*$") {
        $secretKey = (& py "-$PythonVersion" -c "import secrets; print(secrets.token_urlsafe(48))").Trim()
        if ($LASTEXITCODE -ne 0 -or -not $secretKey) {
            throw "No se pudo generar una SECRET_KEY segura."
        }
        $backendEnvironment = [regex]::Replace(
            $backendEnvironment,
            "(?m)^SECRET_KEY=.*$",
            "SECRET_KEY=$secretKey"
        )
        Set-Content "backend\.env" $backendEnvironment -NoNewline
        Write-Host "Se generó una SECRET_KEY local. No compartas backend\.env."
    }

    if (-not (Test-Path $pythonExecutable)) {
        Invoke-CheckedCommand "py" @("-$PythonVersion", "-m", "venv", $pythonEnvironment)
    }
    $venvVersion = & $pythonExecutable --version 2>&1
    if ($venvVersion -notmatch "^Python $([regex]::Escape($PythonVersion))(\.|$)") {
        throw "El entorno .venv existente usa '$venvVersion'; se requiere Python $PythonVersion. Renómbralo manualmente y vuelve a ejecutar."
    }

    Invoke-CheckedCommand $pythonExecutable @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-CheckedCommand $pythonExecutable @("-m", "pip", "install", "-r", "backend\requirements-dev.txt")
    Invoke-CheckedCommand "npm.cmd" @("--prefix", "frontend", "ci")

    $currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $pathEntries = @($currentUserPath -split ";" | Where-Object { $_ })
    if (-not ($pathEntries | Where-Object { $_.TrimEnd("\") -ieq $repositoryRoot.TrimEnd("\") })) {
        $updatedUserPath = (@($pathEntries) + $repositoryRoot) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $updatedUserPath, "User")
        Write-Host "Se agregó la carpeta del repositorio al PATH del usuario."
        Write-Warning "Cierra y vuelve a abrir la terminal para habilitar start-backend, start-pago y start-frontend."
    }

    if (-not $SkipDocker) {
        if (Get-Command docker -ErrorAction SilentlyContinue) {
            Invoke-CheckedCommand "docker" @("compose", "up", "-d", "db", "redis")
        }
        else {
            Write-Warning "Docker no está instalado. Se prepararon Python y Angular; instala Docker Desktop y ejecuta 'docker compose up -d db redis'."
        }
    }

    Write-Host ""
    Write-Host "Entornos locales preparados."
    Write-Host "Comandos disponibles tras abrir una terminal nueva: start-backend, start-pago y start-frontend."
    Write-Warning "La base Docker conserva el SQL de pagos antiguo; aún se requiere preparar/alinear los esquemas operativos antes de usar la API."
}
finally {
    Pop-Location
}
