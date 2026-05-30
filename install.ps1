<#
.SYNOPSIS
    Install okta-skills into AI agent skill directories.
.DESCRIPTION
    Creates symlinks for each skill in the appropriate directories for
    Claude Code, Cursor, Windsurf, GitHub Copilot, and Gemini.

    Symlinks require either Administrator privileges or Developer Mode enabled
    (Settings > System > For developers > Developer Mode).
.PARAMETER Global
    Install into global AI agent skill directories.
.PARAMETER Local
    Install into project-level skill directories.
    Defaults to the current directory if no path is provided.
.EXAMPLE
    .\install.ps1 -Global
.EXAMPLE
    .\install.ps1 -Local C:\projects\my-project
.EXAMPLE
    .\install.ps1 -Global -Local
#>
param(
    [switch]$Global,
    [string]$Local
)

$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir = Join-Path $Repo "skills"

$InstallGlobal = $Global.IsPresent
$LocalPath = $null

if ($PSBoundParameters.ContainsKey('Local')) {
    if ([string]::IsNullOrEmpty($Local)) {
        $LocalPath = (Get-Location).Path
    } else {
        $LocalPath = (Resolve-Path $Local).Path
    }
}

if (-not $InstallGlobal -and -not $LocalPath) {
    Write-Host "Usage: install.ps1 [-Global] [-Local [PATH]]"
    Write-Host ""
    Write-Host "  -Global          Install into global AI agent skill directories"
    Write-Host "  -Local [PATH]    Install into project-level skill directories"
    Write-Host "                   (defaults to current directory if PATH is omitted)"
    Write-Host ""
    Write-Host "Both flags can be combined."
    exit 1
}

function Install-Skills {
    param([string]$DestDir, [string]$Label)

    Write-Host $Label
    Write-Host "  $DestDir"

    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }

    Get-ChildItem -Path $SkillsDir -Directory | ForEach-Object {
        $skill = $_.FullName
        $name  = $_.Name
        $link  = Join-Path $DestDir $name

        if (Test-Path $link) {
            $item = Get-Item $link -Force
            if ($item.LinkType -eq 'SymbolicLink') {
                Remove-Item $link -Force
                New-Item -ItemType SymbolicLink -Path $link -Target $skill | Out-Null
                Write-Host "  updated: $name"
            } else {
                Write-Host "  skipped: $name (exists and is not a symlink)"
            }
        } else {
            try {
                New-Item -ItemType SymbolicLink -Path $link -Target $skill -ErrorAction Stop | Out-Null
                Write-Host "  linked:  $name"
            } catch {
                Write-Host "  error:   $name — $_"
                Write-Host "           Symlinks require Administrator privileges or Developer Mode."
            }
        }
    }
}

if ($InstallGlobal) {
    Install-Skills (Join-Path $HOME ".claude\skills")                "claude (global)"
    Install-Skills (Join-Path $HOME ".codeium\windsurf\skills")      "windsurf (global)"
    Install-Skills (Join-Path $HOME ".copilot\skills")               "copilot (global)"
    Install-Skills (Join-Path $HOME ".gemini\skills")                "gemini (global)"
    Write-Host "cursor — no global skills directory"
    Write-Host ""
}

if ($LocalPath) {
    Install-Skills (Join-Path $LocalPath ".claude\skills")   "claude (local)"
    Install-Skills (Join-Path $LocalPath ".cursor\skills")   "cursor (local)"
    Install-Skills (Join-Path $LocalPath ".windsurf\skills") "windsurf (local)"
    Install-Skills (Join-Path $LocalPath ".github\skills")   "copilot (local)"
    Install-Skills (Join-Path $LocalPath ".gemini\skills")   "gemini (local)"
    Write-Host ""
}

Write-Host "Done."
