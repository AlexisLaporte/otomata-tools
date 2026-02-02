#!/usr/bin/env python3
"""
Create Memento Demo Presentation

Creates a professional demo presentation showcasing Memento's slide generation
capabilities, including tested features and upcoming image functionality.

Structure:
1. Cover slide - Title
2. Use cases - Why automate presentations?
3. Features - Memento capabilities (6 columns)
4. Workflow - How it works (2 columns)
5. Layouts - Available layouts
6. Images - Current capabilities
7. Images - Next tests (6 columns)
8. Conclusion - Call to action

Usage:
    python3 create-demo-presentation.py
"""

import sys
sys.path.insert(0, 'lib')

from slides_client import SlidesClient
from generate_slides import load_credentials_path


# Content for each slide
SLIDE_CONTENT = {
    'cover': {
        'title': 'Memento',
        'subtitle': 'Génération Automatique de Présentations Professionnelles'
    },
    'use_cases': {
        'title': 'Pourquoi automatiser vos présentations ?',
        'body': """Gain de temps considérable
Les équipes se concentrent sur le contenu, pas la mise en forme

Cohérence visuelle garantie
Templates corporate respectés automatiquement

Réutilisabilité maximale
Formats YAML/Markdown faciles à modifier et réutiliser

Intégration API
Génération depuis n'importe quelle source de données"""
    },
    'features': {
        'title': 'Capacités de Memento',
        'columns': [
            {'label': 'Formats YAML', 'text': 'Définition déclarative des slides en YAML ou Markdown simple'},
            {'label': 'Templates 321', 'text': 'Utilisation des templates corporate 321 Studio avec préservation du thème'},
            {'label': 'Layouts variés', 'text': 'Support de tous les layouts : titre, colonnes, corps, combinaisons'},
            {'label': 'Texte formaté', 'text': 'Préservation automatique du formatage défini par les placeholders'},
            {'label': 'Images intégrées', 'text': 'Upload Drive, URLs publiques, placeholders layouts, positionnement'},
            {'label': 'API Drive', 'text': 'Création et partage automatique dans Google Shared Drives'}
        ]
    },
    'workflow': {
        'title': 'Comment ça marche ?',
        'left_column': """Définition en YAML/Markdown

• Structure déclarative simple
• Contenu en Markdown
• Références aux layouts
• Images locales ou URLs
• Métadonnées de présentation""",
        'right_column': """Présentation finalisée

• Création depuis template 321
• Application automatique des layouts
• Formatage préservé (placeholders)
• Images uploadées et insérées
• Partage automatique sur Drive"""
    },
    'layouts': {
        'title': 'Layouts disponibles et testés',
        'body': """Layouts basiques :
• TITLE - Page de couverture
• TITLE_AND_BODY - Titre et corps de texte
• BLANK - Slide vierge pour contenu personnalisé

Layouts multi-colonnes :
• TITLE_AND_TWO_COLUMNS - Titre et 2 colonnes
• CUSTOM_1_1_1 - Titre et 6 colonnes (layout spécial)

Layouts avancés :
• Tous les layouts du template 321 Corporate disponibles
• Préservation automatique du thème et du formatage
• Matching intelligent des placeholders par type et index"""
    },
    'images_current': {
        'title': 'Images : Fonctionnalités implémentées',
        'body': """1. Upload vers Google Drive (slides_client.py:422-466)
   • Upload de fichiers locaux vers Drive
   • Génération automatique d'URLs publiques
   • Support de tous types MIME images

2. Insertion directe avec coordonnées (slides_client.py:377-420)
   • Positionnement précis en unités EMU
   • Dimensions personnalisables
   • URLs publiques requises

3. Remplacement de placeholders (slides_client.py:539-563)
   • Identification automatique des placeholders images
   • Modes CENTER_INSIDE et CENTER_CROP
   • Intégration layouts natifs

4. Intégration depuis Markdown (generate_slides.py:67-378)
   • Extraction automatique ![alt](url)
   • Distribution multi-colonnes
   • Paths MEMENTO /api/media/ supportés"""
    },
    'images_next': {
        'title': 'Prochains tests : Scénarios images',
        'columns': [
            {'label': 'Upload local', 'text': 'Upload d\'images locales depuis filesystem vers Drive puis insertion'},
            {'label': 'URLs publiques', 'text': 'Insertion d\'images depuis URLs HTTP/HTTPS publiquement accessibles'},
            {'label': 'Placeholders layouts', 'text': 'Remplacement de placeholders images dans layouts prédéfinis'},
            {'label': 'Positionnement manuel', 'text': 'Insertion précise avec coordonnées X/Y et dimensions personnalisées'},
            {'label': 'MEMENTO /api/media/', 'text': 'Support chemins /api/media/runs/{id}/ pour intégration pipeline'},
            {'label': 'Distribution auto', 'text': 'Positionnement automatique d\'images multiples (centré, distribué)'}
        ]
    },
    'conclusion': {
        'title': 'Prêt à automatiser vos présentations ?',
        'subtitle': 'Memento transforme vos données en slides professionnelles'
    }
}


def find_layout_slides(client, presentation_id):
    """Find slide IDs for each layout type we need"""

    pres = client.get_presentation(presentation_id)

    # Map layout names to their IDs
    layout_map = {}
    for layout in pres.get('layouts', []):
        layout_name = layout.get('layoutProperties', {}).get('name', '')
        layout_map[layout_name] = layout['objectId']

    # Map layout IDs to example slide IDs
    slide_examples = {}

    for slide in pres.get('slides', []):
        layout_id = slide.get('slideProperties', {}).get('layoutObjectId')

        # Find layout name
        for layout_name, lid in layout_map.items():
            if lid == layout_id:
                if layout_name not in slide_examples:
                    slide_examples[layout_name] = slide['objectId']
                break

    return slide_examples, layout_map


def main():
    # Initialize client
    credentials_path = load_credentials_path()
    print(f"✓ Credentials loaded from {credentials_path}")

    client = SlidesClient(credentials_path)
    print("✓ Client initialized\n")

    # Source presentation (321 Corporate Template)
    source_presentation_id = '1suLRTL-52yLCN_gLX9kNx385xQu7AeeYhaH0iSyXsao'

    print("=" * 80)
    print("STEP 1: Analyze template layouts")
    print("=" * 80)

    slide_examples, layout_map = find_layout_slides(client, source_presentation_id)

    print(f"✓ Found {len(layout_map)} layouts in template:")
    for name, layout_id in sorted(layout_map.items()):
        example = slide_examples.get(name, 'N/A')
        print(f"  • {name}: {layout_id} (example: {example})")

    print("\n" + "=" * 80)
    print("STEP 2: Create presentation from template")
    print("=" * 80)

    folder_id = '1wjxfCabSucwo5sNtdQ2F7aR9g3JzkwE2'  # special_memento

    presentation = client.create_presentation(
        title="Memento - Génération Automatique de Slides",
        folder_id=folder_id,
        template_id=source_presentation_id
    )

    presentation_id = presentation['presentationId']
    print(f"✓ Created presentation: {presentation['title']}")
    print(f"  ID: {presentation_id}")

    # Delete all template slides
    print("\n  Removing template slides...")
    template_slides = client.get_slide_ids(presentation_id)

    if len(template_slides) > 1:
        requests = []
        for slide_id in template_slides[1:]:
            requests.append({'deleteObject': {'objectId': slide_id}})

        client.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()

    client.slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={'requests': [{'deleteObject': {'objectId': template_slides[0]}}]}
    ).execute()
    print(f"  ✓ Presentation ready")

    print("\n" + "=" * 80)
    print("STEP 3: Create slides with content")
    print("=" * 80)

    # Define slides to create
    slides_to_create = [
        ('TITLE', 'cover', 'Cover slide'),
        ('TITLE_AND_BODY', 'use_cases', 'Use cases'),
        ('CUSTOM_1_1_1', 'features', 'Features (6 columns)'),
        ('TITLE_AND_TWO_COLUMNS', 'workflow', 'Workflow'),
        ('TITLE_AND_BODY', 'layouts', 'Layouts available'),
        ('TITLE_AND_BODY', 'images_current', 'Images - Current'),
        ('CUSTOM_1_1_1', 'images_next', 'Images - Next tests'),
        ('TITLE', 'conclusion', 'Conclusion'),
    ]

    created_slides = []

    for i, (layout_name, content_key, description) in enumerate(slides_to_create, 1):
        print(f"\n{i}. Creating: {description}")
        print(f"   Layout: {layout_name}")

        # Get example slide for this layout
        if layout_name not in slide_examples:
            print(f"   ⚠ Layout {layout_name} not found, skipping")
            continue

        source_slide_id = slide_examples[layout_name]

        # Copy slide
        new_slide_id = client.copy_slide_to_presentation(
            source_presentation_id=source_presentation_id,
            source_slide_id=source_slide_id,
            target_presentation_id=presentation_id,
            preserve_layout=True
        )

        print(f"   ✓ Copied: {source_slide_id} → {new_slide_id}")

        # Get placeholders in the new slide
        text_objects = client.get_text_objects_in_slide(presentation_id, new_slide_id)
        content = SLIDE_CONTENT[content_key]

        # Fill content based on layout type
        if layout_name == 'TITLE':
            # Title slide: title + subtitle
            for obj in text_objects:
                if 'title' in content and len(obj['text'].strip()) > 0:
                    client.edit_text(presentation_id, obj['objectId'], content['title'])
                    content.pop('title')  # Remove to handle subtitle next
                elif 'subtitle' in content:
                    client.edit_text(presentation_id, obj['objectId'], content['subtitle'])

        elif layout_name == 'TITLE_AND_BODY':
            # Title + body: first is title, second is body
            if len(text_objects) >= 1 and 'title' in content:
                client.edit_text(presentation_id, text_objects[0]['objectId'], content['title'])
            if len(text_objects) >= 2 and 'body' in content:
                client.edit_text(presentation_id, text_objects[1]['objectId'], content['body'])

        elif layout_name == 'TITLE_AND_TWO_COLUMNS':
            # Title + 2 columns
            if len(text_objects) >= 1 and 'title' in content:
                client.edit_text(presentation_id, text_objects[0]['objectId'], content['title'])
            if len(text_objects) >= 2 and 'left_column' in content:
                client.edit_text(presentation_id, text_objects[1]['objectId'], content['left_column'])
            if len(text_objects) >= 3 and 'right_column' in content:
                client.edit_text(presentation_id, text_objects[2]['objectId'], content['right_column'])

        elif layout_name == 'CUSTOM_1_1_1':
            # Title + 6 columns (title + 6 labels + 6 descriptions)
            if 'title' in content:
                client.edit_text(presentation_id, text_objects[0]['objectId'], content['title'])

            if 'columns' in content:
                # Assuming structure: 1 title + 6 descriptions + 6 labels
                # Need to match based on actual placeholder structure
                columns = content['columns']

                # Try to fill columns (this may need adjustment based on actual layout)
                for idx, col in enumerate(columns):
                    if idx * 2 + 1 < len(text_objects):
                        # Fill description
                        client.edit_text(presentation_id, text_objects[idx * 2 + 1]['objectId'], col['text'])
                    if idx * 2 + 2 < len(text_objects):
                        # Fill label
                        client.edit_text(presentation_id, text_objects[idx * 2 + 2]['objectId'], col['label'])

        print(f"   ✓ Content filled")
        created_slides.append({'id': new_slide_id, 'title': description})

    print(f"\n✓ Created {len(created_slides)} slides")

    print("\n" + "=" * 80)
    print("STEP 4: Share presentation")
    print("=" * 80)

    client.share_presentation(presentation_id)
    url = client.get_presentation_url(presentation_id)

    print(f"\n✓ Presentation shared successfully!")
    print(f"\n📊 View your presentation:")
    print(f"   {url}")
    print()

    print("=" * 80)
    print("✓ DEMO PRESENTATION CREATED")
    print("=" * 80)
    print(f"""
Summary:
  • {len(created_slides)} slides created
  • Template 321 Corporate theme preserved
  • Professional content about Memento capabilities
  • Image features showcased (current + next tests)

Slides:
""")
    for i, slide in enumerate(created_slides, 1):
        print(f"  {i}. {slide['title']}")

    print(f"\nPresentation URL:\n{url}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
