<#
.SYNOPSIS
    Flujo completo de Docker: BUILD -> RUN -> TEST -> PUSH (Windows / PowerShell).

.DESCRIPTION
    1. BUILD: construye la imagen con tres etiquetas: <version>, latest y sha-<commit>.
    2. RUN:   arranca un contenedor temporal y espera a que esté "healthy".
    3. TEST:  ejecuta scripts/smoke_test.py contra el contenedor y comprueba que no corre como root.
    4. PUSH:  (solo con -Push) publica todas las etiquetas en Docker Hub.

.EXAMPLE
    .\scripts\docker_flow.ps1 -DockerHubUser martaarias
    .\scripts\docker_flow.ps1 -DockerHubUser martaarias -Version 1.0.0 -Push
#>
param(
    [Parameter(Mandatory = $true)][string]$DockerHubUser,
    [string]$ImageName = "tienda-online-api",
    [string]$Version = "1.0.0",
    [int]$HostPort = 8000,
    [switch]$Push
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)   # raíz del repositorio

$image     = "$($DockerHubUser.ToLower())/$ImageName"
$sha       = (git rev-parse --short HEAD).Trim()
$container = "tienda-api-smoke"
$python    = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Comprobar($que) { if ($LASTEXITCODE -ne 0) { throw "Falló: $que (código $LASTEXITCODE)" } }
function Eliminar-Contenedor {
    if (docker ps -aq --filter "name=^$container$") { docker rm -f $container | Out-Null }
}

# ------------------------------------------------------------------ BUILD
Paso "1/4 BUILD  -> ${image}:$Version, ${image}:latest, ${image}:sha-$sha"
docker build --build-arg APP_VERSION=$Version `
    -t "${image}:$Version" -t "${image}:latest" -t "${image}:sha-$sha" .
Comprobar "docker build"
docker image ls $image

# ------------------------------------------------------------------ RUN
Paso "2/4 RUN    -> contenedor '$container' en http://localhost:$HostPort"
Eliminar-Contenedor
docker run -d --name $container -p "${HostPort}:8000" "${image}:$Version" | Out-Null
Comprobar "docker run"

try {
    $estado = ""
    for ($i = 0; $i -lt 30 -and $estado -ne "healthy"; $i++) {
        Start-Sleep -Seconds 1
        $estado = docker inspect --format "{{.State.Health.Status}}" $container
    }
    Write-Host "Estado de salud del contenedor: $estado"
    if ($estado -ne "healthy") { throw "El contenedor no llegó a estado healthy" }

    # -------------------------------------------------------------- TEST
    Paso "3/4 TEST   -> smoke test + usuario no root"
    & $python scripts/smoke_test.py "http://localhost:$HostPort"
    Comprobar "smoke test"

    $usuario = (docker exec $container whoami).Trim()
    Write-Host "El proceso se ejecuta como: $usuario"
    if ($usuario -eq "root") { throw "El contenedor no debería ejecutarse como root" }
}
finally {
    Write-Host "`n--- Últimas líneas del log del contenedor ---"
    docker logs --tail 15 $container
    Eliminar-Contenedor
}

# ------------------------------------------------------------------ PUSH
if ($Push) {
    Paso "4/4 PUSH   -> Docker Hub (requiere 'docker login' previo)"
    docker push --all-tags $image
    Comprobar "docker push"
    Write-Host "`nImagen publicada: https://hub.docker.com/r/$image" -ForegroundColor Green
}
else {
    Write-Host "`n4/4 PUSH omitido. Vuelve a ejecutar con -Push para publicar en Docker Hub." -ForegroundColor Yellow
}
Write-Host "`nFlujo completado correctamente." -ForegroundColor Green
