# Payload Folder

This folder is generated for Dashboard++ build context.

- `engine_scripts/`: staged scripts from `O:/_Theophysics_v3/00_SYSTEM/00_ENGINE/01_ENGINE`
- `backend_scripts/`: staged scripts from `O:/999_IGNORE/Obsidian Programs/Python_Backend`
- `script_inventory.csv`: generated inventory

To regenerate:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\stage_dashboard_payload.ps1 -RepoPath .
```
