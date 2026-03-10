# Google Slides - Text Editing Guide

Documentation for the new text editing capabilities added to the Google Slides tool.

## New Methods

### 1. `get_slide_ids(presentation_id)`

Get list of all slide IDs in a presentation.

```python
from lib.slides_client import SlidesClient

client = SlidesClient('path/to/credentials.json')
slide_ids = client.get_slide_ids('presentation_id')

print(f"Found {len(slide_ids)} slides")
for i, slide_id in enumerate(slide_ids):
    print(f"Slide {i}: {slide_id}")
```

### 2. `get_text_objects_in_slide(presentation_id, slide_id)`

Get all text objects (shapes with text) in a slide.

```python
text_objects = client.get_text_objects_in_slide(
    'presentation_id',
    'slide_id'
)

for obj in text_objects:
    print(f"Object ID: {obj['objectId']}")
    print(f"Type: {obj['shapeType']}")
    print(f"Text: {obj['text']}")
    print(f"Position: {obj['transform']}")
    print(f"Size: {obj['size']}")
```

### 3. `get_text_content(presentation_id, slide_id, object_id)`

Get text content from a specific shape or text box.

```python
text = client.get_text_content(
    'presentation_id',
    'slide_id',
    'object_id'
)

print(f"Text content: {text}")
```

### 4. `edit_text(presentation_id, object_id, new_text, start_index=None, end_index=None)`

Edit text in an existing shape or text box.

**Replace all text:**
```python
client.edit_text(
    'presentation_id',
    'object_id',
    'New text content'
)
```

**Replace specific range:**
```python
# Replace characters 5-10
client.edit_text(
    'presentation_id',
    'object_id',
    'Inserted text',
    start_index=5,
    end_index=10
)
```

**Replace from position to end:**
```python
# Replace everything from position 10 onwards
client.edit_text(
    'presentation_id',
    'object_id',
    'New ending',
    start_index=10
)
```

### 5. `replace_all_text(presentation_id, find_text, replace_text, match_case=False, page_object_ids=None)`

Global find/replace across entire presentation or specific slides.

**Replace all occurrences:**
```python
result = client.replace_all_text(
    'presentation_id',
    '{{company}}',
    'Acme Corporation'
)

occurrences = result['replies'][0]['replaceAllText']['occurrencesChanged']
print(f"Replaced {occurrences} occurrences")
```

**Replace in specific slides only:**
```python
result = client.replace_all_text(
    'presentation_id',
    '{{date}}',
    '2025-11-13',
    page_object_ids=['slide_id_1', 'slide_id_2']
)
```

**Case-sensitive replacement:**
```python
client.replace_all_text(
    'presentation_id',
    'COMPANY',
    'Acme Corp',
    match_case=True
)
```

### 6. `duplicate_slide(presentation_id, slide_id, insertion_index=None)`

Duplicate a slide within the same presentation using native API.

**Basic duplication:**
```python
# Duplicate a slide (will be inserted after original)
new_slide_id = client.duplicate_slide(
    'presentation_id',
    'slide_id_to_duplicate'
)
print(f"Created duplicate: {new_slide_id}")
```

**Duplicate at specific position:**
```python
# Duplicate and insert at position 3
new_slide_id = client.duplicate_slide(
    'presentation_id',
    'slide_id_to_duplicate',
    insertion_index=3
)
```

### 7. `copy_slide_to_presentation(source_presentation_id, source_slide_id, target_presentation_id, insertion_index=None, preserve_layout=True)`

Copy a slide from one presentation to another by recreating all elements.

**Copy single slide:**
```python
# Copy slide from template to new presentation
new_slide_id = client.copy_slide_to_presentation(
    source_presentation_id='1rA2YmY...',  # Template ID
    source_slide_id='g13ce2af5b70_0_0',
    target_presentation_id='1abc...',      # Target presentation
    preserve_layout=True
)
print(f"Copied slide: {new_slide_id}")
```

**Copy multiple slides:**
```python
# Copy first 3 slides from template
template_id = '1rA2YmY...'
target_id = '1abc...'

# Get source slides
source_slides = client.get_slide_ids(template_id)

# Copy each slide
for slide_id in source_slides[:3]:
    new_id = client.copy_slide_to_presentation(
        source_presentation_id=template_id,
        source_slide_id=slide_id,
        target_presentation_id=target_id
    )
    print(f"Copied {slide_id} → {new_id}")
```

**Copy without preserving layout:**
```python
# Copy slide with blank layout
new_slide_id = client.copy_slide_to_presentation(
    source_presentation_id='1rA2YmY...',
    source_slide_id='g13ce2af5b70_0_0',
    target_presentation_id='1abc...',
    preserve_layout=False  # Use blank layout
)
```

## Complete Workflow Examples

### Example 1: Update specific text in first slide

```python
from lib.slides_client import SlidesClient

# Initialize
client = SlidesClient('credentials.json')
presentation_id = '1abc...'

# Get first slide
slide_ids = client.get_slide_ids(presentation_id)
first_slide = slide_ids[0]

# Find text objects
text_objects = client.get_text_objects_in_slide(presentation_id, first_slide)

# Update first text object
if text_objects:
    client.edit_text(
        presentation_id,
        text_objects[0]['objectId'],
        'Updated title text'
    )
    print("✓ Updated first text object")
```

### Example 2: Replace all placeholders

```python
from lib.slides_client import SlidesClient

client = SlidesClient('credentials.json')
presentation_id = '1abc...'

# Replace multiple placeholders
placeholders = {
    '{{company}}': 'Acme Corporation',
    '{{date}}': '2025-11-13',
    '{{amount}}': '$1,000,000',
    '{{author}}': 'John Smith'
}

for find, replace in placeholders.items():
    result = client.replace_all_text(
        presentation_id,
        find,
        replace
    )
    count = result['replies'][0]['replaceAllText']['occurrencesChanged']
    print(f"✓ Replaced {find}: {count} occurrence(s)")
```

### Example 3: Search and update specific text

```python
from lib.slides_client import SlidesClient

client = SlidesClient('credentials.json')
presentation_id = '1abc...'

# Get all slides
slide_ids = client.get_slide_ids(presentation_id)

# Search for specific text
for slide_id in slide_ids:
    text_objects = client.get_text_objects_in_slide(presentation_id, slide_id)

    for obj in text_objects:
        if 'Company Name' in obj['text']:
            # Update this text
            client.edit_text(
                presentation_id,
                obj['objectId'],
                'Acme Corporation'
            )
            print(f"✓ Updated text in slide {slide_id}")
            break
```

### Example 4: Create presentation from template and customize

```python
from lib.slides_client import SlidesClient

client = SlidesClient('credentials.json')
template_id = '1rA2Ym...'  # 321 template

# Create from template
presentation = client.create_presentation(
    title='Q1 2025 Report',
    template_id=template_id
)
presentation_id = presentation['presentationId']

# Replace all placeholders
replacements = {
    '{{quarter}}': 'Q1 2025',
    '{{revenue}}': '$5.2M',
    '{{growth}}': '+24%',
    '{{client}}': 'Acme Corp'
}

for find, replace in replacements.items():
    client.replace_all_text(presentation_id, find, replace)

# Share and get URL
client.share_presentation(presentation_id)
url = client.get_presentation_url(presentation_id)

print(f"✓ Created and customized presentation: {url}")
```

### Example 5: Update specific slides only

```python
from lib.slides_client import SlidesClient

client = SlidesClient('credentials.json')
presentation_id = '1abc...'

# Get slides
slide_ids = client.get_slide_ids(presentation_id)

# Update only slides 0, 2, 4
target_slides = [slide_ids[i] for i in [0, 2, 4] if i < len(slide_ids)]

# Replace text only in these slides
client.replace_all_text(
    presentation_id,
    '{{status}}',
    'Updated',
    page_object_ids=target_slides
)

print(f"✓ Updated {len(target_slides)} slides")
```

### Example 6: Build presentation from template slides

```python
from lib.slides_client import SlidesClient

client = SlidesClient('credentials.json')
template_id = '1rA2YmY...'  # 321 corporate template

# Create new presentation
presentation = client.create_presentation('Q4 2025 Pitch Deck')
presentation_id = presentation['presentationId']

# Get all template slides
template_slides = client.get_slide_ids(template_id)

# Copy specific slides we need (intro, features, pricing, contact)
slides_to_copy = [template_slides[0], template_slides[5], template_slides[12], template_slides[20]]

for slide_id in slides_to_copy:
    new_id = client.copy_slide_to_presentation(
        source_presentation_id=template_id,
        source_slide_id=slide_id,
        target_presentation_id=presentation_id,
        preserve_layout=True
    )
    print(f"✓ Copied slide {slide_id}")

# Customize copied slides
client.replace_all_text(presentation_id, '{{client}}', 'Acme Corp')
client.replace_all_text(presentation_id, '{{date}}', '2025-11-13')

# Share
client.share_presentation(presentation_id)
url = client.get_presentation_url(presentation_id)
print(f"✓ Created: {url}")
```

### Example 7: Duplicate slides for repetitive content

```python
from lib.slides_client import SlidesClient

client = SlidesClient('credentials.json')
presentation_id = '1abc...'

# Get slide to duplicate (team member template)
slide_ids = client.get_slide_ids(presentation_id)
team_template_slide = slide_ids[5]

# Create 5 team member slides
team_members = [
    {'name': 'Alice Smith', 'role': 'CEO'},
    {'name': 'Bob Johnson', 'role': 'CTO'},
    {'name': 'Carol White', 'role': 'CFO'},
    {'name': 'David Brown', 'role': 'COO'},
    {'name': 'Eve Green', 'role': 'CMO'}
]

for i, member in enumerate(team_members):
    # Duplicate template slide
    new_slide_id = client.duplicate_slide(
        presentation_id,
        team_template_slide,
        insertion_index=6 + i
    )

    # Customize with team member info
    client.replace_all_text(
        presentation_id,
        '{{name}}',
        member['name'],
        page_object_ids=[new_slide_id]
    )
    client.replace_all_text(
        presentation_id,
        '{{role}}',
        member['role'],
        page_object_ids=[new_slide_id]
    )

    print(f"✓ Created slide for {member['name']}")
```

## Use Cases

### Use Case 1: Automated Report Generation

Generate monthly reports from template with dynamic data:
```python
# Create from template
presentation = client.create_presentation('Monthly Report', template_id)

# Update with current data
client.replace_all_text(presentation_id, '{{month}}', 'November 2025')
client.replace_all_text(presentation_id, '{{revenue}}', '$1.2M')
client.replace_all_text(presentation_id, '{{growth}}', '+15%')
```

### Use Case 2: Client Presentations

Customize pitch decks for each client:
```python
# Copy template
presentation = client.create_presentation('Pitch - Acme', template_id)

# Customize for client
client.replace_all_text(presentation_id, '{{client_name}}', 'Acme Corporation')
client.replace_all_text(presentation_id, '{{industry}}', 'Technology')
client.replace_all_text(presentation_id, '{{proposal_date}}', '2025-11-13')
```

### Use Case 3: Bulk Updates

Update existing presentations with new branding:
```python
presentation_ids = ['1abc...', '1def...', '1ghi...']

for pres_id in presentation_ids:
    client.replace_all_text(pres_id, 'Old Company Name', 'New Company Name')
    client.replace_all_text(pres_id, 'old-logo.png', 'new-logo.png')
    print(f"✓ Updated {pres_id}")
```

### Use Case 4: Build Custom Decks from Template Library

Select and combine slides from multiple templates:
```python
# Template library
templates = {
    'intro': ('1abc...', [0, 1, 2]),      # First 3 slides
    'features': ('1def...', [5, 7, 9]),   # Specific feature slides
    'case_studies': ('1ghi...', [0, 3]),  # Case study slides
    'closing': ('1jkl...', [10])          # Final slide
}

# Create new deck
deck = client.create_presentation('Custom Client Deck')
deck_id = deck['presentationId']

# Copy slides from each template
for section, (template_id, slide_indices) in templates.items():
    template_slides = client.get_slide_ids(template_id)

    for idx in slide_indices:
        if idx < len(template_slides):
            client.copy_slide_to_presentation(
                source_presentation_id=template_id,
                source_slide_id=template_slides[idx],
                target_presentation_id=deck_id
            )
            print(f"✓ Added {section} slide {idx}")

# Customize
client.replace_all_text(deck_id, '{{client}}', 'Acme Corp')
```

### Use Case 5: Multi-Language Presentations

Duplicate slides and translate content:
```python
# Original presentation
pres_id = '1abc...'
slide_ids = client.get_slide_ids(pres_id)

# For each slide, create duplicate and translate
translations = {
    'Welcome': 'Bienvenue',
    'Features': 'Fonctionnalités',
    'Contact': 'Contactez-nous'
}

for slide_id in slide_ids:
    # Duplicate slide
    new_slide_id = client.duplicate_slide(pres_id, slide_id)

    # Replace English with French
    for english, french in translations.items():
        client.replace_all_text(
            pres_id,
            english,
            french,
            page_object_ids=[new_slide_id]
        )

    print(f"✓ Translated slide {slide_id}")
```

## API Limitations

1. **Cross-presentation slide copying limitations**
   - Native REST API `duplicateObject` only works within same presentation
   - Workaround implemented: `copy_slide_to_presentation()` recreates slide elements
   - Supports: text shapes, images, positioning, layouts
   - May not preserve: animations, videos, complex charts, speaker notes
   - Images must be accessible (same Drive account or public URLs)
   - Use `duplicate_slide()` for same-presentation copies (native, reliable)

2. **Text indices are 0-based**
   - Text positions use 0-based Unicode character indices
   - Newlines count as characters (paragraph markers)
   - Be careful with emoji and multi-byte characters

3. **Batch operations are atomic**
   - All requests in a `batchUpdate` are atomic
   - If one fails, all fail
   - Use try/except for error handling

4. **Storage quota**
   - Creating many presentations can exceed Drive quota
   - Consider cleanup/archival strategies
   - Use shared drives for team projects

## Best Practices

1. **Use placeholders for templates**
   ```yaml
   # In .slides.yaml file
   slides:
     - title: "{{client_name}} - Proposal"
       content: |
         Prepared for: {{client_name}}
         Date: {{date}}
         Amount: {{amount}}
   ```

2. **Read before editing**
   ```python
   # Get current content first
   text_objects = client.get_text_objects_in_slide(pres_id, slide_id)
   for obj in text_objects:
       if 'specific text' in obj['text']:
           # Now edit it
           client.edit_text(pres_id, obj['objectId'], 'new text')
   ```

3. **Use replace_all_text for simple cases**
   ```python
   # Simpler than searching and editing
   client.replace_all_text(pres_id, '{{placeholder}}', 'value')
   ```

4. **Share presentations after creation**
   ```python
   client.create_presentation(title, template_id)
   client.share_presentation(presentation_id)  # Make accessible
   ```

## Troubleshooting

**Error: "The user's Drive storage quota has been exceeded"**
- Solution: Delete old presentations or upgrade storage

**Error: "Invalid requests[0].deleteText: The end index should not be greater than the text length"**
- Solution: Use `type: 'ALL'` or verify text length before editing

**Text not found**
- Check if object_id is correct
- Verify slide_id is valid
- Use `get_text_objects_in_slide()` to inspect structure

**Replace not working**
- Check exact text match (case-sensitive by default)
- Use `match_case=False` for case-insensitive
- Verify placeholder syntax matches exactly

## References

- [Google Slides API Documentation](https://developers.google.com/slides/api)
- [Text Editing Requests](https://developers.google.com/slides/api/reference/rest/v1/presentations/request#deleteTextrequest)
- [Google Slides Python Client](https://developers.google.com/slides/api/quickstart/python)

## Summary of Available Methods

**Text Editing (Phase 1 - Complete):**
1. `get_slide_ids()` - List all slides in presentation
2. `get_text_objects_in_slide()` - Find text objects in a slide
3. `get_text_content()` - Read text from specific object
4. `edit_text()` - Replace text in shapes
5. `replace_all_text()` - Global find/replace

**Slide Copying (Phase 1 - Complete):**
6. `duplicate_slide()` - Duplicate within same presentation (native API)
7. `copy_slide_to_presentation()` - Copy between presentations (element recreation)

**Future Enhancements (Phase 2):**
- Google Apps Script bridge for native cross-presentation copying
- Preserve animations and videos
- Copy speaker notes
- Handle complex charts and diagrams
- Batch slide operations with progress tracking

The current implementation provides full text editing and slide copying capabilities for most use cases.
