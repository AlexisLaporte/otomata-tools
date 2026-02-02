#!/usr/bin/env python3
"""
Test script: Copy slides from template and edit text content

Demonstrates:
1. Copying slides from one presentation to another (copy_slide_to_presentation)
2. Editing text content in copied slides (get_text_objects_in_slide, edit_text)
3. Complete workflow for customizing slides from a template

Usage:
    python3 test-copy-and-edit.py
"""

import sys
sys.path.insert(0, 'lib')

from slides_client import SlidesClient
from generate_slides import load_credentials_path


def main():
    # Initialize client
    credentials_path = load_credentials_path()
    print(f"✓ Credentials loaded from {credentials_path}")

    client = SlidesClient(credentials_path)
    print("✓ Client initialized\n")

    # Source presentation (321 Corporate Template)
    source_presentation_id = '1suLRTL-52yLCN_gLX9kNx385xQu7AeeYhaH0iSyXsao'

    print("=" * 80)
    print("STEP 1: Inspect source presentation")
    print("=" * 80)

    # Get slides from source
    source_slides = client.get_slide_ids(source_presentation_id)
    print(f"✓ Source presentation has {len(source_slides)} slides")
    print(f"  URL: https://docs.google.com/presentation/d/{source_presentation_id}/edit")

    # Inspect first slide
    first_slide_id = source_slides[0]
    text_objects = client.get_text_objects_in_slide(source_presentation_id, first_slide_id)

    print(f"\n✓ First slide contains {len(text_objects)} text objects:")
    for obj in text_objects:
        print(f"  - {obj['objectId']}: \"{obj['text'][:50]}...\"" if len(obj['text']) > 50
              else f"  - {obj['objectId']}: \"{obj['text']}\"")

    print("\n" + "=" * 80)
    print("STEP 2: Create new presentation FROM TEMPLATE")
    print("=" * 80)

    # Create new presentation in Shared Drive FROM 321 TEMPLATE
    # This preserves the theme (colors, fonts, styles)
    folder_id = '1wjxfCabSucwo5sNtdQ2F7aR9g3JzkwE2'  # special_memento

    presentation = client.create_presentation(
        title="Test - Copy & Edit Slide Demo",
        folder_id=folder_id,
        template_id=source_presentation_id  # Copy from 321 template to preserve theme
    )

    presentation_id = presentation['presentationId']
    print(f"✓ Created presentation from 321 template: {presentation['title']}")
    print(f"  ID: {presentation_id}")
    print(f"  Theme preserved: ✓")

    # Delete all slides from the copied template (we'll add specific ones)
    print("\n  Removing template slides...")
    template_slides = client.get_slide_ids(presentation_id)
    print(f"  Found {len(template_slides)} slides to remove")

    # Delete all slides except the first one (can't delete all)
    requests = []
    for slide_id in template_slides[1:]:  # Keep first, delete rest
        requests.append({'deleteObject': {'objectId': slide_id}})

    if requests:
        client.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()
        print(f"  ✓ Removed {len(requests)} template slides")

    # Delete the first slide too
    first_slide = template_slides[0]
    client.slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={'requests': [{'deleteObject': {'objectId': first_slide}}]}
    ).execute()
    print(f"  ✓ Presentation ready (all template slides removed)")

    print("\n" + "=" * 80)
    print("STEP 3: Copy slides from template")
    print("=" * 80)

    # Copy first 3 slides from template
    copied_slides = []
    for i, slide_id in enumerate(source_slides[:3], 1):
        print(f"\nCopying slide {i}/3...")

        new_slide_id = client.copy_slide_to_presentation(
            source_presentation_id=source_presentation_id,
            source_slide_id=slide_id,
            target_presentation_id=presentation_id,
            preserve_layout=True
        )

        copied_slides.append(new_slide_id)
        print(f"  ✓ Copied: {slide_id} → {new_slide_id}")

    print(f"\n✓ Successfully copied {len(copied_slides)} slides")

    print("\n" + "=" * 80)
    print("STEP 4: Edit text in copied slides")
    print("=" * 80)

    # Edit first copied slide
    first_copied_slide = copied_slides[0]
    print(f"\nEditing first copied slide: {first_copied_slide}")

    # Get text objects in copied slide
    text_objects = client.get_text_objects_in_slide(presentation_id, first_copied_slide)

    print(f"✓ Found {len(text_objects)} text objects to edit")

    # Edit each text object
    for i, obj in enumerate(text_objects, 1):
        object_id = obj['objectId']
        original_text = obj['text']

        # Add "[MODIFIED]" prefix to demonstrate editing
        new_text = f"[MODIFIED] {original_text}"

        print(f"\n  {i}. Editing object {object_id}:")
        print(f"     Original: \"{original_text[:60]}...\"" if len(original_text) > 60
              else f"     Original: \"{original_text}\"")

        client.edit_text(
            presentation_id=presentation_id,
            object_id=object_id,
            new_text=new_text
        )

        print(f"     Modified: \"{new_text[:60]}...\"" if len(new_text) > 60
              else f"     Modified: \"{new_text}\"")

    print("\n✓ Text editing completed")

    print("\n" + "=" * 80)
    print("STEP 5: Share presentation and display link")
    print("=" * 80)

    # Share presentation
    client.share_presentation(presentation_id)
    url = client.get_presentation_url(presentation_id)

    print(f"\n✓ Presentation shared successfully!")
    print(f"\n📊 View your presentation:")
    print(f"   {url}")
    print()

    print("=" * 80)
    print("✓ TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"""
Summary:
  - Copied 3 slides from template
  - Modified text in first slide (added [MODIFIED] prefix)
  - Presentation is ready to view

Next steps:
  - Open the presentation link above
  - Verify that the first slide shows modified text
  - Check that layouts and formatting are preserved
""")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
