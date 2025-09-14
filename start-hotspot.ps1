# start-hotspot.ps1
# Forces execution policy bypass only for this script
# Looks for a profile called 'Loopback' (rename if yours is different)

$profile = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType=WindowsRuntime]::GetConnectionProfiles() | Where-Object { $_.ProfileName -eq 'Loopback' }

if ($null -eq $profile) {
    Write-Host "Loopback adapter profile not found. Check adapter name!"
    exit 1
}

$tether = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType=WindowsRuntime]::CreateFromConnectionProfile($profile)
$tether.StartTetheringAsync() | Out-Null

Write-Host "Hotspot started using Loopback adapter."
