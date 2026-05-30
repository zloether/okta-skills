<#
.SYNOPSIS
    Install okta-skills into AI agent skill directories.
.DESCRIPTION
    Creates symlinks for each skill in the appropriate directories for
    Claude Code, Cursor, Windsurf, GitHub Copilot, and Gemini.

    Symlinks require either Administrator privileges or Developer Mode enabled
    (Settings > System > For developers > Developer Mode).

    If no agent flags are provided, all agents are installed.
.PARAMETER Global
    Install into global AI agent skill directories.
.PARAMETER Local
    Install into project-level skill directories.
    Defaults to the current directory if no path is provided.
.PARAMETER Claude
    Install for Claude Code only.
.PARAMETER Cursor
    Install for Cursor only.
.PARAMETER Windsurf
    Install for Windsurf only.
.PARAMETER Copilot
    Install for GitHub Copilot only.
.PARAMETER Gemini
    Install for Gemini only.
.EXAMPLE
    .\install.ps1 -Global
.EXAMPLE
    .\install.ps1 -Local C:\projects\my-project -Claude -Cursor
.EXAMPLE
    .\install.ps1 -Global -Local
#>
param(
    [switch]$Global,
    [string]$Local,
    [switch]$Claude,
    [switch]$Cursor,
    [switch]$Windsurf,
    [switch]$Copilot,
    [switch]$Gemini
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
    Write-Host "Usage: install.ps1 [-Global] [-Local [PATH]] [-Claude] [-Cursor] [-Windsurf] [-Copilot] [-Gemini]"
    Write-Host ""
    Write-Host "  -Global      Install into global AI agent skill directories"
    Write-Host "  -Local PATH  Install into project-level skill directories"
    Write-Host "               (defaults to current directory if PATH is omitted)"
    Write-Host ""
    Write-Host "  -Claude      Install for Claude Code only"
    Write-Host "  -Cursor      Install for Cursor only"
    Write-Host "  -Windsurf    Install for Windsurf only"
    Write-Host "  -Copilot     Install for GitHub Copilot only"
    Write-Host "  -Gemini      Install for Gemini only"
    Write-Host ""
    Write-Host "If no agent flags are provided, all agents are installed."
    exit 1
}

# If no agent flags given, enable all
$anyAgent = $Claude -or $Cursor -or $Windsurf -or $Copilot -or $Gemini
$OptClaude   = $Claude.IsPresent   -or -not $anyAgent
$OptCursor   = $Cursor.IsPresent   -or -not $anyAgent
$OptWindsurf = $Windsurf.IsPresent -or -not $anyAgent
$OptCopilot  = $Copilot.IsPresent  -or -not $anyAgent
$OptGemini   = $Gemini.IsPresent   -or -not $anyAgent

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
    if ($OptClaude)   { Install-Skills (Join-Path $HOME ".claude\skills")           "claude (global)" }
    if ($OptWindsurf) { Install-Skills (Join-Path $HOME ".codeium\windsurf\skills") "windsurf (global)" }
    if ($OptCopilot)  { Install-Skills (Join-Path $HOME ".copilot\skills")          "copilot (global)" }
    if ($OptGemini)   { Install-Skills (Join-Path $HOME ".gemini\skills")           "gemini (global)" }
    if ($OptCursor)   { Write-Host "cursor — no global skills directory" }
    Write-Host ""
}

if ($LocalPath) {
    if ($OptClaude)   { Install-Skills (Join-Path $LocalPath ".claude\skills")   "claude (local)" }
    if ($OptCursor)   { Install-Skills (Join-Path $LocalPath ".cursor\skills")   "cursor (local)" }
    if ($OptWindsurf) { Install-Skills (Join-Path $LocalPath ".windsurf\skills") "windsurf (local)" }
    if ($OptCopilot)  { Install-Skills (Join-Path $LocalPath ".github\skills")   "copilot (local)" }
    if ($OptGemini)   { Install-Skills (Join-Path $LocalPath ".gemini\skills")   "gemini (local)" }
    Write-Host ""
}

Write-Host "Done."
