# Dashboard Navigator (Dashboard++) Install

## Files to copy
Copy these files into your vault plugin folder:
- `main.js`
- `manifest.json`
- `styles.css`

## Vault install path
1. Create/open:
   - `O:\_Theophysics_v3\.obsidian\plugins\dashboard-navigator`
2. Copy the three files above into that folder.
3. Ensure community plugin entry exists in:
   - `O:\_Theophysics_v3\.obsidian\community-plugins.json`
   - Add plugin id: `dashboard-navigator`
4. In Obsidian:
   - Settings → Community Plugins → Reload plugins
   - Enable **Dashboard Navigator**

## First-time Dashboard++ setup
1. Open plugin settings and find **Dashboard++** section.
2. Verify default paths:
   - Script registry: `O:/_Theophysics_v3/00_SYSTEM/00_ENGINE/01_ENGINE/launchers/script_registry.json`
   - Context rules: `O:/_Theophysics_v3/00_SYSTEM/00_ENGINE/01_ENGINE/launchers/context_rules.json`
   - Log path: `O:/_Theophysics_v3/00_SYSTEM/06_ADMIN/BUILD_LOGS/dashboard_pp_runs.log`
3. Run commands from command palette:
   - `Dashboard++: Generate folder dashboards`
   - `Dashboard++: Open current folder dashboard`
   - `Dashboard++: Open script panel for current folder`
