# Cloud Handoff Prompt — Dashboard++ + Script Overlay
Date: 2026-03-05

## Recommendation
Use this repo as the base:
- https://github.com/YellowKidokc/dashboard-navigator-for-obsidian

Why:
- It is a real Obsidian plugin codebase (TypeScript, manifest, build pipeline).
- It already has dashboard and navigator UI foundations.
- Best path to your “GUI over scripts + recursive folder dashboards”.

## Difficulty (honest)
- MVP (dashboard generator + context script panel, no destructive actions): **Medium**
- Full production (safe execution, logs, context rules, polished UI): **Medium-High**
- Not impossible. Very doable with staged scope.

## Paste This Into Claude Code / Codex Cloud
```text
You are implementing Dashboard++ for Obsidian by extending this repo:
https://github.com/YellowKidokc/dashboard-navigator-for-obsidian

Goal:
Turn Dashboard Navigator into a folder-aware command center that:
1) Auto-generates recursive dashboards (root + folder dashboards + INDEX notes),
2) Shows runnable script actions filtered by folder context,
3) Supports safe execution of Python / PowerShell / BAT scripts with confirmations and logs.

Working assumptions:
- Main vault path is O:/_Theophysics_v3
- Engine room is O:/_Theophysics_v3/00_SYSTEM/00_ENGINE/01_ENGINE
- Registry files:
  - O:/_Theophysics_v3/00_SYSTEM/00_ENGINE/01_ENGINE/launchers/script_registry.json
  - O:/_Theophysics_v3/00_SYSTEM/00_ENGINE/01_ENGINE/launchers/context_rules.json

Required deliverables:

1) New plugin section: “Dashboard++”
- Add command: “Dashboard++: Generate folder dashboards”
- Add command: “Dashboard++: Open current folder dashboard”
- Add command: “Dashboard++: Open script panel for current folder”

2) Recursive dashboard generation engine
- Generate/update:
  - DB_HOME.md (root dashboard)
  - DB_<FOLDER>.md for key folders
  - INDEX.md in folders where missing
- Include metadata frontmatter:
  - type: dashboard
  - scope: folder
  - folder_path
  - parent_dashboard
  - root_dashboard
  - status: active
  - last_generated: YYYY-MM-DD
- Use protected regions:
  - <!-- AUTO:START --> ... <!-- AUTO:END -->
  - <!-- MANUAL:START --> ... <!-- MANUAL:END -->
- Never overwrite MANUAL section.

3) Script overlay panel (folder context)
- Read script_registry.json and context_rules.json.
- Detect current folder from active file.
- Filter scripts by context rules and tags.
- Show for each script:
  - name
  - type
  - description
  - safety flag (safe/unsafe)
- Provide actions:
  - Run
  - Copy command
  - Open script file

4) Safe execution model
- For unsafe scripts or destructive tags, show confirmation modal.
- Add execution logs:
  - O:/_Theophysics_v3/00_SYSTEM/06_ADMIN/BUILD_LOGS/dashboard_pp_runs.log
- Log timestamp, folder, script id, command, status, duration, stderr snippet.

5) Settings tab additions
- Toggle: enable script execution
- Toggle: show only safe scripts
- Ignore folders list
- Max generation depth
- Dashboard filename prefix (default DB_)

6) Acceptance tests
- Test command generates DB_HOME + at least one DB_<FOLDER> from a sample folder tree.
- Re-running generation preserves MANUAL section.
- Script panel shows different script sets for two different folders.
- One safe script execution succeeds and is logged.
- One blocked/unsafe run requires confirmation.

7) Output package
- Commit all code changes.
- Build plugin artifacts:
  - main.js
  - manifest.json
  - styles.css
- Produce INSTALL.md with exact vault install steps.
- Provide a short TEST_REPORT.md with pass/fail for acceptance tests.

Constraints:
- Keep existing dashboard-navigator features working.
- Do not remove existing commands.
- Keep code modular and typed.
- Avoid hardcoding vault paths except as defaults in settings.
```

## What To Ask Them For When Done
- ZIP with built plugin files (`main.js`, `manifest.json`, `styles.css`)
- `INSTALL.md`
- `TEST_REPORT.md`
- Branch/commit hash

## Fast Install Path After They Finish
1. Drop plugin folder into:
   `O:\_Theophysics_v3\.obsidian\plugins\dashboard-navigator`
2. Add plugin id to:
   `O:\_Theophysics_v3\.obsidian\community-plugins.json`
3. Reload Obsidian
