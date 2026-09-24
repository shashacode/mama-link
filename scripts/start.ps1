$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv/Scripts/python.exe')) { throw 'Run scripts/setup.ps1 first.' }
& ./.venv/Scripts/python.exe -m uvicorn mama_link.api:app --host 127.0.0.1 --port 8000
