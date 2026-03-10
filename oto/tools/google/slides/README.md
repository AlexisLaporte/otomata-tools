# Google Slides Generator Tool

Generate Google Slides presentations from `.slides.yaml` files with the 321 theme.

## Overview

This tool converts MEMENTO `.slides.yaml` files into Google Slides presentations using the Google Slides API. It automatically applies the 321 theme and uses native Google Slides layouts.

## Features

- **YAML to Google Slides** - Direct conversion from `.slides.yaml` format
- **321 Theme by Default** - Automatically applies the 321 corporate theme
- **Native Layouts** - Uses Google Slides layouts (not manual text boxes)
- **35 Layouts Available** - All 321 custom layouts accessible
- **Markdown Conversion** - Automatic conversion of markdown to plain text
- **Public Sharing** - Optional public access control
- **Folder Organization** - Automatic creation in shared Drive folder
- **Template Support** - Can use any Google Slides presentation as theme template

## Installation

```bash
pip install -r requirements.txt
```

## Authentication

Uses the same Google service account as `google-drive` tool. Place credentials at:

```bash
tools/google-slides/.keys/gdrive-key.json
```

Required scopes:
- `https://www.googleapis.com/auth/presentations`
- `https://www.googleapis.com/auth/drive.file`

## Usage

### Basic Usage

```bash
python3 generate_slides.py --input presentation.slides.yaml
```

Returns: URL to the created presentation

### With Public Sharing

```bash
python3 generate_slides.py --input presentation.slides.yaml --share
```

Creates a presentation that anyone with the link can view.

### In Specific Folder

```bash
python3 generate_slides.py \
  --input presentation.slides.yaml \
  --folder-id 1abc2def3ghi4jkl
```

### JSON Output

```bash
python3 generate_slides.py \
  --input presentation.slides.yaml \
  --output json
```

Returns:
```json
{
  "id": "1abc2def3ghi4jkl",
  "title": "My Presentation",
  "url": "https://docs.google.com/presentation/d/1abc2def3ghi4jkl/edit",
  "slides_count": 5
}
```

## Supported Layouts (YAML)

Le tool mappe 5 layouts YAML vers les layouts Google Slides natifs:

| YAML | Google Slides | Description |
|------|--------------|-------------|
| `default` | Title and body | Titre + contenu (layout standard) |
| `hero` | Title only | Titre seul, grand format |
| `2-columns` | Title and two columns | Titre + 2 colonnes |
| `3-columns` | Title and body | Pas de 3-col natif, utilise default |
| `2-panels` | Section title and description | Titre + description |

### Exemple basique

```yaml
title: Ma Présentation
date: 2025-11-06

slides:
  - title: Slide Standard
    layout: default
    content: |
      Contenu avec **markdown**
      - Liste
      - Points

  - title: Titre Seul
    layout: hero

  - title: Deux Colonnes
    layout: 2-columns
    content: |
      Colonne gauche
      ---
      Colonne droite
```

## Thème 321 - 35 Layouts Disponibles

Le thème 321 contient **35 layouts** dont:

**Layouts standards (11):**
- Title slide, Section header, Title and body
- Title and two columns, Title only, One column text
- Main point, Section title and description
- Caption, Big number, Blank

**Layouts custom 321 (24):**
- **Table of contents** - Sommaire
- **Quote** - Citations
- **Thanks** - Page de remerciements
- **Title and three columns** - 3 colonnes native ⭐
- **Title and four columns** - 4 colonnes ⭐
- **Title and six columns** - 6 colonnes ⭐
- **Numbers and text** - Chiffres + texte
- **Background** - Fonds personnalisés
- Et 16 autres variations...

**Note:** Les layouts custom ne sont pas encore mappés dans le YAML. Utilisez les 5 layouts de base, puis modifiez manuellement dans Google Slides si besoin.

**Voir les layouts:** Ouvrez `321-LAYOUTS.md` ou la présentation de test pour voir visuellement chaque layout.

## YAML Format

Based on MEMENTO `.slides.yaml` format:

```yaml
title: Presentation Title
subtitle: Optional subtitle
date: 2025-11-06
author: Author Name

slides:
  - title: First Slide
    layout: hero

  - title: Content Slide
    layout: default
    content: |
      # Main Point
      - Bullet 1
      - Bullet 2

  - title: Comparison
    layout: 2-columns
    content: |
      **Option A**
      - Feature 1
      - Feature 2
      ---
      **Option B**
      - Feature X
      - Feature Y
```

## Markdown Support

The tool converts markdown to plain text:
- Headers (`#`, `##`, `###`) → Plain text
- Bold/Italic (`**`, `*`, `__`, `_`) → Removed
- Links `[text](url)` → `text`
- Lists maintained as plain text

## Examples

See `example.slides.yaml` for a complete example.

## Limitations

- No custom fonts or colors (uses Google Slides defaults)
- Markdown conversion is basic (no tables, complex formatting)
- Images are uploaded to Google Drive and inserted automatically
- Image positioning is automatic (centered or distributed horizontally)

## Related Tools

- `google-drive` - File management, upload/download
- Memento Slides Viewer - Web viewer for `.slides.yaml` files

## API Reference

See `lib/slides_client.py` for the Google Slides API wrapper.

Key methods:
- `create_presentation(title)` - Create new presentation
- `add_slide(presentation_id, layout)` - Add slide
- `add_text_box(...)` - Add text content
- `share_presentation(...)` - Set permissions
- `move_to_folder(...)` - Organize in Drive
