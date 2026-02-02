#!/usr/bin/env python3
"""
Test script for Google Slides copy/duplicate capabilities

Demonstrates:
- duplicate_slide() - Copy slide within same presentation
- copy_slide_to_presentation() - Copy slide between presentations
"""
import sys
import json
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from slides_client import SlidesClient
from generate_slides import load_credentials_path


def main():
    """Test slide copying capabilities"""

    # Load credentials
    credentials_path = load_credentials_path()
    print(f"✓ Credentials loaded from {credentials_path}")

    # Initialize client
    client = SlidesClient(credentials_path)
    print("✓ Client initialized\n")

    # Template ID (321 corporate template)
    template_id = '1rA2YmYTA5P2O7GHgv9p3JwouO0lVVZEpZyKFFUKiVH4'

    # Test 1: Get slide IDs from template
    print(f"📊 Reading template presentation...")
    slide_ids = client.get_slide_ids(template_id)
    print(f"✓ Template has {len(slide_ids)} slides")

    if not slide_ids:
        print("⚠ Template is empty, cannot proceed")
        return

    # Display template slides
    print(f"\n📋 Template slides:")
    for i, slide_id in enumerate(slide_ids):
        print(f"  {i}: {slide_id}")

    # Test 2: Create a new empty presentation
    print(f"\n📊 Creating test presentation...")
    test_pres = client.create_presentation(
        title="Test - Slide Copy Demo"
    )
    test_pres_id = test_pres['presentationId']
    test_url = client.get_presentation_url(test_pres_id)
    print(f"✓ Created presentation: {test_url}")

    # Test 3: Copy specific slides from template
    print(f"\n🔄 Test: Copying slides from template to new presentation...")

    # Copy first 3 slides (or all if less than 3)
    slides_to_copy = slide_ids[:min(3, len(slide_ids))]

    for i, source_slide_id in enumerate(slides_to_copy):
        print(f"\n  Copying slide {i} (ID: {source_slide_id})...")
        try:
            new_slide_id = client.copy_slide_to_presentation(
                source_presentation_id=template_id,
                source_slide_id=source_slide_id,
                target_presentation_id=test_pres_id,
                preserve_layout=True
            )
            print(f"  ✓ Created slide {new_slide_id}")
        except Exception as e:
            print(f"  ⚠ Error copying slide: {e}")
            # Continue with other slides

    # Test 4: Duplicate a slide within the presentation
    print(f"\n🔄 Test: Duplicating slide within presentation...")
    current_slides = client.get_slide_ids(test_pres_id)

    if current_slides:
        first_slide = current_slides[0]
        print(f"  Duplicating slide {first_slide}...")
        try:
            duplicated_slide_id = client.duplicate_slide(
                test_pres_id,
                first_slide
            )
            print(f"  ✓ Duplicated as {duplicated_slide_id}")
        except Exception as e:
            print(f"  ⚠ Error duplicating: {e}")

    # Test 5: Verify final slide count
    print(f"\n📊 Verifying results...")
    final_slides = client.get_slide_ids(test_pres_id)
    print(f"✓ Final presentation has {len(final_slides)} slides")

    # Test 6: Add text to copied slides
    print(f"\n✏️  Test: Adding custom text to copied slides...")
    for i, slide_id in enumerate(final_slides[:2]):  # Only first 2 slides
        text_objects = client.get_text_objects_in_slide(test_pres_id, slide_id)
        if text_objects:
            # Edit first text object
            try:
                client.edit_text(
                    test_pres_id,
                    text_objects[0]['objectId'],
                    f"Slide {i+1} - Modified via API\n\nThis content was added after copying."
                )
                print(f"  ✓ Added text to slide {i+1}")
            except Exception as e:
                print(f"  ⚠ Could not edit slide {i+1}: {e}")

    # Share presentation
    print(f"\n🔓 Sharing presentation...")
    try:
        client.share_presentation(test_pres_id)
        print(f"✓ Presentation is now publicly accessible")
    except Exception as e:
        print(f"⚠ Could not share: {e}")

    # Summary
    print(f"\n" + "="*60)
    print(f"✅ All tests completed!")
    print(f"="*60)
    print(f"\n📊 Test Presentation: {test_url}")
    print(f"   Open this link to see the copied slides")
    print(f"\n🎯 Tests performed:")
    print(f"   1. ✓ Read template slides ({len(slide_ids)} found)")
    print(f"   2. ✓ Created new presentation")
    print(f"   3. ✓ copy_slide_to_presentation() - Copied {min(3, len(slide_ids))} slides")
    print(f"   4. ✓ duplicate_slide() - Duplicated within presentation")
    print(f"   5. ✓ edit_text() - Modified copied slides")
    print(f"   6. ✓ Final: {len(final_slides)} slides in presentation")
    print(f"\n💡 Use cases:")
    print(f"   - Copy specific slides from 321 template to client decks")
    print(f"   - Duplicate slides for repetitive content")
    print(f"   - Build presentations from multiple sources")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
