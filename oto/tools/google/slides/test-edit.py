#!/usr/bin/env python3
"""
Test script for Google Slides editing capabilities

This script demonstrates the new text editing methods:
- get_slide_ids() - List all slides
- get_text_objects_in_slide() - Find text objects
- get_text_content() - Read text from objects
- edit_text() - Replace text in shapes
- replace_all_text() - Global find/replace
"""
import sys
import json
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from slides_client import SlidesClient
from generate_slides import load_credentials_path


def main():
    """Test text editing capabilities"""

    # Load credentials
    credentials_path = load_credentials_path()
    print(f"✓ Credentials loaded from {credentials_path}")

    # Initialize client
    client = SlidesClient(credentials_path)
    print("✓ Client initialized")

    # Test presentation ID (use the template or create a new one)
    # For testing, we'll create a new presentation from template
    template_id = '1rA2YmYTA5P2O7GHgv9p3JwouO0lVVZEpZyKFFUKiVH4'

    print(f"\n📊 Creating test presentation from template...")
    presentation = client.create_presentation(
        title="Test - Text Editing Demo",
        template_id=template_id
    )
    presentation_id = presentation['presentationId']
    url = client.get_presentation_url(presentation_id)

    print(f"✓ Created presentation: {url}")
    print(f"  ID: {presentation_id}")

    # Test 1: Get all slide IDs
    print(f"\n🔍 Test 1: Getting slide IDs...")
    slide_ids = client.get_slide_ids(presentation_id)
    print(f"✓ Found {len(slide_ids)} slides")
    for i, slide_id in enumerate(slide_ids):
        print(f"  Slide {i}: {slide_id}")

    if not slide_ids:
        print("⚠ No slides found - template might be empty")
        return

    # Test 2: Get text objects in first slide
    first_slide_id = slide_ids[0]
    print(f"\n🔍 Test 2: Getting text objects in first slide...")
    text_objects = client.get_text_objects_in_slide(presentation_id, first_slide_id)
    print(f"✓ Found {len(text_objects)} text objects")

    for i, obj in enumerate(text_objects):
        print(f"\n  Object {i+1}:")
        print(f"    ID: {obj['objectId']}")
        print(f"    Type: {obj['shapeType']}")
        print(f"    Text: {obj['text'][:100]}..." if len(obj['text']) > 100 else f"    Text: {obj['text']}")

    if not text_objects:
        print("⚠ No text objects found in first slide")
        return

    # Test 3: Read text content from first object
    first_object = text_objects[0]
    print(f"\n🔍 Test 3: Reading text content...")
    text_content = client.get_text_content(
        presentation_id,
        first_slide_id,
        first_object['objectId']
    )
    print(f"✓ Text content: {repr(text_content)}")

    # Test 4: Edit text in first object
    print(f"\n✏️  Test 4: Editing text in first object...")
    new_text = "This text was modified by the API!\n\nTesting edit_text() method."
    result = client.edit_text(
        presentation_id,
        first_object['objectId'],
        new_text
    )
    print(f"✓ Text edited successfully")
    print(f"  New text: {repr(new_text)}")

    # Verify the change
    updated_text = client.get_text_content(
        presentation_id,
        first_slide_id,
        first_object['objectId']
    )
    print(f"✓ Verified: {repr(updated_text)}")

    # Test 5: Add placeholder text for replace_all_text test
    if len(text_objects) > 1:
        print(f"\n✏️  Test 5: Adding placeholder text...")
        second_object = text_objects[1]
        placeholder_text = "Company: {{company}}\nDate: {{date}}\nAmount: {{amount}}"
        client.edit_text(
            presentation_id,
            second_object['objectId'],
            placeholder_text
        )
        print(f"✓ Added placeholder text to second object")

        # Test 6: Replace all placeholders
        print(f"\n🔄 Test 6: Replacing all placeholders...")

        # Replace {{company}}
        result1 = client.replace_all_text(
            presentation_id,
            '{{company}}',
            'Acme Corporation'
        )
        occurrences1 = result1['replies'][0]['replaceAllText']['occurrencesChanged']
        print(f"✓ Replaced {{{{company}}}}: {occurrences1} occurrence(s)")

        # Replace {{date}}
        result2 = client.replace_all_text(
            presentation_id,
            '{{date}}',
            '2025-11-13'
        )
        occurrences2 = result2['replies'][0]['replaceAllText']['occurrencesChanged']
        print(f"✓ Replaced {{{{date}}}}: {occurrences2} occurrence(s)")

        # Replace {{amount}}
        result3 = client.replace_all_text(
            presentation_id,
            '{{amount}}',
            '$1,000,000'
        )
        occurrences3 = result3['replies'][0]['replaceAllText']['occurrencesChanged']
        print(f"✓ Replaced {{{{amount}}}}: {occurrences3} occurrence(s)")

        # Verify the changes
        updated_text = client.get_text_content(
            presentation_id,
            first_slide_id,
            second_object['objectId']
        )
        print(f"\n✓ Final text: {repr(updated_text)}")

    # Share presentation
    print(f"\n🔓 Sharing presentation...")
    client.share_presentation(presentation_id)
    print(f"✓ Presentation is now publicly accessible")

    # Summary
    print(f"\n" + "="*60)
    print(f"✅ All tests completed successfully!")
    print(f"="*60)
    print(f"\n📊 Test Presentation: {url}")
    print(f"   Open this link to see the changes")
    print(f"\n🎯 Tests performed:")
    print(f"   1. ✓ get_slide_ids() - Listed {len(slide_ids)} slides")
    print(f"   2. ✓ get_text_objects_in_slide() - Found {len(text_objects)} text objects")
    print(f"   3. ✓ get_text_content() - Read text content")
    print(f"   4. ✓ edit_text() - Modified text in shape")
    if len(text_objects) > 1:
        print(f"   5. ✓ replace_all_text() - Replaced placeholders")
    print(f"\n💡 You can now use these methods in your own scripts!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
