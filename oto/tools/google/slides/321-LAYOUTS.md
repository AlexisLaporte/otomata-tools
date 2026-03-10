# 321 Template - Layout Reference

This document describes the 12 essential layouts selected for use with the 321 Google Slides template.

Template ID: `1rA2YmYTA5P2O7GHgv9p3JwouO0lVVZEpZyKFFUKiVH4`

## Selected Layouts

| YAML Name | Display Name | Fill Strategy | Placeholders | Usage |
|-----------|-------------|---------------|--------------|-------|
| `title-slide` | Title slide | `title_only` | TITLE, SUBTITLE | Page de titre (première slide) |
| `default` | Title and body | `title_and_body` | TITLE, BODY | Slide standard avec titre + texte |
| `hero` | Main point | `title_only` | TITLE | Grand titre impact |
| `2-columns` | Title and two columns | `title_and_columns` | TITLE, SUBTITLE, SUBTITLE | Titre + 2 colonnes |
| `3-columns` | Title and three columns | `title_and_columns` | TITLE, SUBTITLE, SUBTITLE, SUBTITLE | Titre + 3 colonnes |
| `section` | Title and text 3 1 | `title_and_body` | TITLE, BODY | Séparateur section (coloré) |
| `section-alt` | Title and text 1 | `title_and_body` | TITLE, BODY | Séparateur section (gris) |
| `blank` | Blank | `blank` | none | Vierge pour grosse image/diagramme |
| `toc` | Table of contents | `title_and_body` | TITLE, BODY | Table des matières |
| `thanks` | Thanks | `title_and_body` | TITLE, BODY | Page de remerciements |
| `numbers` | Numbers and text | `title_and_body` | TITLE, BODY | 3 blocs numérotés |
| `numbers-5` | Numbers and text 1 | `title_and_body` | TITLE, BODY | 5 blocs numérotés |

## Fill Strategies

### `title_only`
- Fills only the TITLE placeholder
- Used for: hero slides, title slides
- YAML fields: `title`, `content` (content goes to SUBTITLE if present)

### `title_and_body`
- Fills TITLE and BODY placeholders
- Used for: default, section, toc, thanks, numbers layouts
- YAML fields: `title`, `content`

### `title_and_columns`
- Fills TITLE and multiple SUBTITLE placeholders (one per column)
- Used for: 2-columns, 3-columns
- YAML fields: `title`, `columns` (list of `{content: ...}`)

### `blank`
- No text filling
- Used for: blank layout (images/diagrams only)

## YAML Examples

### Title Slide
```yaml
- title: "My Presentation"
  layout: title-slide
  content: |
    Subtitle text here
    Date and author info
```

### Default Slide
```yaml
- title: "Slide Title"
  layout: default
  content: |
    Bullet points or paragraph text
    - Point 1
    - Point 2
```

### Hero Slide
```yaml
- title: "Big impactful statement"
  layout: hero
```

### 2-Column Slide
```yaml
- title: "Two Topics"
  layout: 2-columns
  columns:
    - content: |
        Left column content
        - Item A
        - Item B
    - content: |
        Right column content
        - Item X
        - Item Y
```

### 3-Column Slide
```yaml
- title: "Three Features"
  layout: 3-columns
  columns:
    - content: |
        Feature 1 description
    - content: |
        Feature 2 description
    - content: |
        Feature 3 description
```

### Section Separator
```yaml
- title: "Part 2: Market Analysis"
  layout: section
  content: |
    Optional subtitle text
```

### Table of Contents
```yaml
- title: "Agenda"
  layout: toc
  content: |
    1. Introduction
    2. Problem Statement
    3. Our Solution
    4. Business Model
    5. Next Steps
```

### Numbers Layout
```yaml
- title: "Three Key Points"
  layout: numbers
  content: |
    1. First Point
    Brief explanation of the first key point

    2. Second Point
    Brief explanation of the second key point

    3. Third Point
    Brief explanation of the third key point
```

### Blank Slide (with image)
```yaml
- title: ""
  layout: blank
  content: |
    ![Architecture Diagram](images/architecture.png)
```

## Adding Images

Images can be added to any layout using Markdown syntax:

```yaml
- title: "Product Screenshot"
  layout: default
  content: |
    Our platform provides:
    - Feature A
    - Feature B

    ![Screenshot](images/product.png)
```

Images are:
1. Extracted from Markdown
2. Uploaded to Google Drive (in `images/` subfolder)
3. Inserted into the slide
4. Positioned automatically (centered if single, distributed horizontally if multiple)

## Technical Details

### Layout Mappings
See `lib/layout_mappings.py` for complete mapping of:
- YAML name → API name
- YAML name → Fill strategy
- YAML name → Expected placeholders

### Content Filling
See `lib/content_filler.py` for implementation of fill strategies:
- `ContentFiller` class handles all text insertion
- Strategy-based approach: each layout has its own filling logic
- Automatic Markdown → plain text conversion
- Placeholder detection and matching

### Adding New Layouts

To add a new layout:

1. **Update `lib/layout_mappings.py`**:
```python
'new-layout': (index, 'API_NAME', 'Display Name', 'Usage description', {
    'strategy': 'title_and_body',  # or 'title_and_columns', etc.
    'placeholders': ['TITLE', 'BODY'],
    'column_count': 2  # if columns layout
})
```

2. **Add strategy to `lib/content_filler.py`** (if new strategy needed):
```python
def _fill_new_strategy(self, slide_id, slide_data):
    # Implementation
    pass
```

3. **Update this documentation** with usage examples

## Other Layouts

The 321 template contains 35 total layouts. The 23 non-selected layouts are listed in `layout_mappings.py` for reference but have no fill strategy defined. They can still be used if needed by adding a fill strategy.
