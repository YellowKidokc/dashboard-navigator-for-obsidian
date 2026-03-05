# Obsidian Page Template System

Dashboard Banner + Sticky Navigation Footer

## Overview

Every note in your vault gets three zones:

```
+---------------------------------------------+
|  ZONE 1: DASHBOARD BANNER (top)             |
|  Category nav - Quick links - Status badge  |
+---------------------------------------------+
|                                             |
|  ZONE 2: CONTENT (scrollable)               |
|  The actual note content                    |
|                                             |
+---------------------------------------------+
|  ZONE 3: STICKY NAV (always visible bottom) |
|  Home  Back  Forward  Recent                |
+---------------------------------------------+
```

Zone 3 stays visible no matter how far you scroll. Zone 1 scrolls with the content but is always at the top when you open the note.

## Requirements

- **Obsidian** v1.1.0+
- **Templater** plugin (for auto-inserting template on new notes)
- **Dataview** plugin (optional, for dynamic banner content like file counts)

## Installation

### Step 1: CSS Snippet

1. Copy `snippets/page-template-system.css` to your vault's `.obsidian/snippets/` folder
2. In Obsidian, go to **Settings > Appearance > CSS Snippets**
3. Click the reload button and enable `page-template-system`

### Step 2: Templater Template

1. Copy `templates/page_template.md` to your vault's template folder (e.g. `_templates/`)
2. In Obsidian, go to **Settings > Templater > Template folder location**
3. Set it to your template folder (e.g. `_templates`)

### Step 3: Create New Notes

Use Templater to create a new note from the `page_template` template. The script will:

- Auto-detect the current folder name for the banner title
- Prompt you to select a note type (Axiom, Theorem, Claim, etc.)
- Prompt you to select a domain (Physics, Theology, etc.)
- Auto-populate prev/next navigation links based on sibling files

## Customization

### Banner Navigation Links

Edit the `banner-nav` section in `page_template.md` to match your vault structure. The default links point to:

- Canon (Canonical Index)
- DT Index (Doctor Thesis Index)
- Master Eq (Master Equation)
- Ten Laws (Ten Laws Canonical Equations)
- 24 Props (24 Properties)

### Footer Navigation

The footer includes:

- **Home** - Links to the current folder's `00_INDEX.md`
- **Back/Forward** - Auto-populated prev/next notes in the folder
- **Recent** - Links to a `_RECENT` note
- **Vault Home** - Links to the global canonical index

### Status Badges

Three status styles are available via CSS classes:

- `draft` - Gold outline badge
- `complete` - Green badge
- `published` - Solid green badge

### Dynamic Content (Dataview)

For live file counts and link stats in the banner, you can use Dataview inline queries:

```markdown
`= "Files: " + length(filter(this.file.folder.files, (f) => f.extension = "md"))`
`= "Links: " + length(this.file.outlinks)`
```

## File Structure

```
page-template/
  README.md              # This file
  snippets/
    page-template-system.css  # CSS snippet for Obsidian
  templates/
    page_template.md     # Templater template with auto-insert script
```
