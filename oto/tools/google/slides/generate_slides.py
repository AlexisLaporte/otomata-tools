#!/usr/bin/env python3
"""
Generate Google Slides presentation from .slides.yaml file

Usage:
    python3 generate_slides.py --input presentation.slides.yaml [--share]
"""
import json
import sys
import time
import yaml
import typer
from typing_extensions import Annotated
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.slides_client import SlidesClient

app = typer.Typer(help="Generate Google Slides from YAML")


def load_credentials_path():
    """Load Google service account credentials path from local .keys directory."""
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    return str(credentials_path)


def load_default_folder():
    """Load default folder ID from .folders file."""
    folders_path = Path(__file__).parent / '.folders'

    if not folders_path.exists():
        return None

    with open(folders_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('DEFAULT_FOLDER='):
                return line.split('=', 1)[1].strip()

    return None


def load_default_template():
    """Load default template ID from .folders file."""
    folders_path = Path(__file__).parent / '.folders'

    if not folders_path.exists():
        return None

    with open(folders_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('DEFAULT_TEMPLATE='):
                return line.split('=', 1)[1].strip()

    return None


def load_slides_yaml(file_path):
    """Load and parse slides YAML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_images_from_markdown(content):
    """
    Extract image references from markdown content

    Returns:
        list: List of dicts with 'alt' (alt text) and 'url' (image URL/path)
    """
    if not content:
        return []

    import re
    # Match markdown images: ![alt text](url)
    pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    matches = re.findall(pattern, content)

    return [{'alt': alt, 'url': url} for alt, url in matches]


def get_google_layout_for_yaml_layout(yaml_layout):
    """
    Map YAML layout to Google Slides layout

    Uses the complete 321 template layout mappings
    """
    from lib.layout_mappings import get_api_name
    return get_api_name(yaml_layout)




def generate_presentation(yaml_path, share=False, folder_id=None, template_id=None, output_format='url'):
    """
    Generate Google Slides presentation from YAML

    Args:
        yaml_path: Path to .slides.yaml file
        share: Make presentation publicly accessible
        folder_id: Optional Google Drive folder ID
        template_id: Optional presentation ID to use as template (for theme)
        output_format: 'url' or 'json'

    Returns:
        dict: Presentation info (id, url, title)
    """
    # Load YAML
    data = load_slides_yaml(yaml_path)

    # Initialize client with credentials from .env.keys
    credentials_path = load_credentials_path()
    client = SlidesClient(credentials_path)

    # Use folder_id or default from .folders
    if folder_id is None:
        folder_id = load_default_folder()

    # Get template_id from YAML, command line, or default (in order of priority)
    if template_id is None:
        template_id = data.get('template_id')
    if template_id is None:
        template_id = load_default_template()

    # Create a parent folder for this deck (deck + images)
    title = data.get('title', 'Untitled Presentation')
    deck_folder_name = title
    print(f"Creating deck folder: {deck_folder_name}")
    deck_folder_id = client.create_folder(deck_folder_name, parent_folder_id=folder_id)

    # Create presentation in the deck folder
    presentation = client.create_presentation(title, folder_id=deck_folder_id, template_id=template_id)
    presentation_id = presentation['presentationId']

    # Remove all slides from template (if template was used)
    if template_id:
        pres = client.get_presentation(presentation_id)
        existing_slides = pres.get('slides', [])

        if existing_slides:
            # Delete all slides in one batch request
            delete_requests = [
                {'deleteObject': {'objectId': slide['objectId']}}
                for slide in existing_slides
            ]

            client.slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': delete_requests}
            ).execute()
    else:
        # Remove default slide for new presentations
        pres = client.get_presentation(presentation_id)
        if pres.get('slides'):
            first_slide_id = pres['slides'][0]['objectId']
            client.slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': [{'deleteObject': {'objectId': first_slide_id}}]}
            ).execute()

    # Get base path for resolving relative image paths
    yaml_base_path = Path(yaml_path).parent

    # Create an "images" subfolder in the deck folder if we have any images
    images_folder_id = None
    has_images = any(
        extract_images_from_markdown(slide.get('content', '')) or
        extract_images_from_markdown('\n\n'.join([col.get('content', '') for col in slide.get('columns', [])]))
        for slide in data.get('slides', [])
    )

    if has_images:
        print(f"Creating images subfolder in {deck_folder_name}/")
        images_folder_id = client.create_folder("images", parent_folder_id=deck_folder_id)

    # Create content filler
    from lib.content_filler import ContentFiller
    filler = ContentFiller(client, presentation_id)

    # Add slides
    slides = data.get('slides', [])
    for slide_data in slides:
        # Map YAML layout to Google Slides layout
        yaml_layout = slide_data.get('layout', 'default')
        google_layout = get_google_layout_for_yaml_layout(yaml_layout)

        # Create slide with native Google layout
        slide_id = client.add_slide(presentation_id, layout=google_layout)

        # Fill content using smart strategy-based filler
        filler.fill_slide(slide_id, yaml_layout, slide_data)

        # Handle single image field (for layouts with image placeholders)
        single_image = slide_data.get('image')
        if single_image:
            # Get image placeholders in this slide
            image_placeholders = client.get_image_placeholders_in_slide(presentation_id, slide_id)

            if image_placeholders:
                image_url = single_image

                # Resolve local paths
                if not image_url.startswith(('http://', 'https://')):
                    if image_url.startswith('/api/media/'):
                        import re
                        match = re.search(r'/api/media/runs/([^/]+)/(.+)', image_url)
                        if match:
                            run_id, file_path = match.groups()
                            project_root = yaml_base_path
                            while project_root.name != '' and not (project_root / 'agents').exists():
                                project_root = project_root.parent
                            local_path = project_root / 'agents' / run_id / file_path
                        else:
                            local_path = yaml_base_path / image_url.lstrip('/')
                    else:
                        local_path = yaml_base_path / image_url

                    # Upload to Drive
                    if local_path.exists():
                        print(f"Uploading image for placeholder: {local_path}")
                        upload_folder = images_folder_id if images_folder_id else folder_id
                        image_url = client.upload_image_to_drive(str(local_path), upload_folder)
                    else:
                        print(f"Warning: Image not found: {local_path}")
                        image_url = None

                # Replace first image placeholder
                if image_url:
                    try:
                        client.replace_image_placeholder(
                            presentation_id,
                            image_placeholders[0],  # Use first placeholder
                            image_url,
                            replace_method='CENTER_INSIDE'
                        )
                        print(f"Replaced image placeholder with: {single_image}")
                    except Exception as e:
                        print(f"Error replacing image placeholder: {e}")
            else:
                print(f"Warning: 'image' field specified but layout has no image placeholder")

        # Extract images for insertion
        columns = slide_data.get('columns', [])

        # Get slide dimensions (standard 16:9 - 10" x 5.625")
        # 1 inch = 914400 EMU
        slide_width = 10 * 914400
        slide_height = 5.625 * 914400

        # Handle column layouts: extract images per column
        if columns and yaml_layout in ['2-columns', '3-columns']:
            # Extract images per column
            images_by_column = []
            for col in columns:
                col_images = extract_images_from_markdown(col.get('content', ''))
                images_by_column.append(col_images)

            # Position images at the top of each column
            num_columns = len(columns)
            column_width = slide_width / num_columns
            margin = 0.5 * 914400  # 0.5 inch margin

            # Smaller images for column layouts
            img_width = column_width - (2 * margin)  # Fit within column
            img_height = img_width * 0.75  # Maintain 4:3 ratio

            # Position: top of each column
            y_top = 1.5 * 914400  # 1.5 inches from top (below title)

            for col_idx, col_images in enumerate(images_by_column):
                if not col_images:
                    continue

                # X position for this column
                x = (col_idx * column_width) + margin

                # Insert first image of column (if multiple, only use first)
                for img_data in col_images[:1]:  # Only first image per column
                    image_url = img_data['url']

                    # Resolve local paths
                    if not image_url.startswith(('http://', 'https://')):
                        # Handle relative paths and /api/media paths
                        if image_url.startswith('/api/media/'):
                            # Convert /api/media/runs/xxx to local path
                            import re
                            match = re.search(r'/api/media/runs/([^/]+)/(.+)', image_url)
                            if match:
                                run_id, file_path = match.groups()
                                # Find the project root (where agents/ folder is)
                                project_root = yaml_base_path
                                while project_root.name != '' and not (project_root / 'agents').exists():
                                    project_root = project_root.parent
                                local_path = project_root / 'agents' / run_id / file_path
                            else:
                                local_path = yaml_base_path / image_url.lstrip('/')
                        else:
                            local_path = yaml_base_path / image_url

                        # Upload to Drive and get public URL
                        if local_path.exists():
                            print(f"Uploading image: {local_path} (column {col_idx + 1})")
                            upload_folder = images_folder_id if images_folder_id else folder_id
                            image_url = client.upload_image_to_drive(str(local_path), upload_folder)
                        else:
                            print(f"Warning: Image not found: {local_path}")
                            continue

                    # Insert image at top of column
                    try:
                        client.insert_image(presentation_id, slide_id, image_url,
                                          int(x), int(y_top), int(img_width), int(img_height))
                        print(f"Inserted image in column {col_idx + 1}: {img_data['alt'] or 'Image'}")
                    except Exception as e:
                        print(f"Error inserting image: {e}")

        else:
            # Standard layouts: extract all images and center them
            all_content = slide_data.get('content', '')
            images = extract_images_from_markdown(all_content)

            if images:
                # Default image dimensions for standard layouts
                img_width = 2.5 * 914400  # 2.5 inches (smaller than before)
                img_height = img_width * 0.75  # Maintain 4:3 ratio
                spacing = 0.5 * 914400

                total_images = len(images)

                for idx, img_data in enumerate(images):
                    image_url = img_data['url']

                    # Resolve local paths
                    if not image_url.startswith(('http://', 'https://')):
                        if image_url.startswith('/api/media/'):
                            import re
                            match = re.search(r'/api/media/runs/([^/]+)/(.+)', image_url)
                            if match:
                                run_id, file_path = match.groups()
                                project_root = yaml_base_path
                                while project_root.name != '' and not (project_root / 'agents').exists():
                                    project_root = project_root.parent
                                local_path = project_root / 'agents' / run_id / file_path
                            else:
                                local_path = yaml_base_path / image_url.lstrip('/')
                        else:
                            local_path = yaml_base_path / image_url

                        if local_path.exists():
                            print(f"Uploading image: {local_path}")
                            upload_folder = images_folder_id if images_folder_id else folder_id
                            image_url = client.upload_image_to_drive(str(local_path), upload_folder)
                        else:
                            print(f"Warning: Image not found: {local_path}")
                            continue

                    # Calculate position (distribute images horizontally)
                    if total_images == 1:
                        # Center single image
                        x = (slide_width - img_width) / 2
                        y = (slide_height - img_height) / 2 + (1 * 914400)
                    else:
                        # Arrange multiple images horizontally
                        total_width = (img_width * total_images) + (spacing * (total_images - 1))
                        start_x = (slide_width - total_width) / 2
                        x = start_x + (idx * (img_width + spacing))
                        y = (slide_height - img_height) / 2 + (1 * 914400)

                # Insert image
                try:
                    client.insert_image(presentation_id, slide_id, image_url,
                                      int(x), int(y), int(img_width), int(img_height))
                    print(f"Inserted image: {img_data['alt'] or 'Image'}")
                except Exception as e:
                    print(f"Error inserting image: {e}")

        # Throttle API requests to avoid rate limiting (60 requests/minute limit)
        # Sleep 2 seconds between slides to stay under limit
        time.sleep(2)

    # Share if requested
    if share:
        client.share_presentation(presentation_id)

    # Get URL
    url = client.get_presentation_url(presentation_id)

    result = {
        'id': presentation_id,
        'title': title,
        'url': url,
        'slides_count': len(slides)
    }

    if output_format == 'json':
        return json.dumps(result, indent=2)
    else:
        return url


@app.command()
def main(
    input: Annotated[str, typer.Option(help="Path to .slides.yaml file")],
    share: Annotated[bool, typer.Option(help="Make presentation public")] = False,
    folder_id: Annotated[Optional[str], typer.Option(help="Google Drive folder ID")] = None,
    template_id: Annotated[Optional[str], typer.Option(help="Presentation ID to use as template (for theme)")] = None,
    output: Annotated[str, typer.Option(help="Output format")] = 'url',
):
    """Generate Google Slides from YAML."""
    if output not in ['url', 'json']:
        print(f"Error: Invalid output format '{output}'. Choose from: url, json", file=sys.stderr)
        raise typer.Exit(1)

    try:
        result = generate_presentation(
            input,
            share=share,
            folder_id=folder_id,
            template_id=template_id,
            output_format=output
        )
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
