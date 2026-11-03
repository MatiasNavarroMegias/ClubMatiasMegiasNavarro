param(
    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl,
    [string]$Email,
    [string]$Password
)

$ErrorActionPreference = "Stop"
$baseUrl = $ApiBaseUrl.TrimEnd("/")

$health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
if ($health.status -ne "ok") {
    throw "El endpoint /health no devolvio estado ok."
}

$openApi = Invoke-RestMethod -Uri "$baseUrl/openapi.json" -Method Get
$requiredPaths = @(
    "/auth/login",
    "/auth/password-recovery/request",
    "/auth/password-recovery/confirm",
    "/venues",
    "/sports-spaces",
    "/reservations",
    "/push-devices",
    "/internal/reminders"
)

foreach ($path in $requiredPaths) {
    if ($null -eq $openApi.paths.$path) {
        throw "Falta el endpoint $path en OpenAPI."
    }
}

Write-Output "Health y OpenAPI correctos."

if ($Email -and $Password) {
    $loginBody = @{
        email = $Email
        password = $Password
    } | ConvertTo-Json
    $login = Invoke-RestMethod `
        -Uri "$baseUrl/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $loginBody

    if ([string]::IsNullOrWhiteSpace($login.access_token)) {
        throw "El login no devolvio un token."
    }

    $headers = @{ Authorization = "Bearer $($login.access_token)" }
    Invoke-RestMethod -Uri "$baseUrl/users/me" -Headers $headers -Method Get | Out-Null
    Invoke-RestMethod -Uri "$baseUrl/venues" -Method Get | Out-Null
    Invoke-RestMethod -Uri "$baseUrl/sports-spaces" -Method Get | Out-Null
    Invoke-RestMethod -Uri "$baseUrl/reservations/upcoming" -Headers $headers -Method Get | Out-Null
    Invoke-RestMethod -Uri "$baseUrl/reservations/history" -Headers $headers -Method Get | Out-Null
    Write-Output "Endpoints publicos y autenticados basicos correctos."
}
