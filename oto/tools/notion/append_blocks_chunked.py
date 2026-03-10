#!/usr/bin/env python3
"""
Append blocks to Notion page with automatic chunking for large files.

Usage:
    python3 append_blocks_chunked.py --page_id abc123 --markdown-file file.md
    python3 append_blocks_chunked.py --page_id abc123 --markdown-file file.md --image path/to/image.png
"""
import json
import re
import sys
import base64
from pathlib import Path
from typing_extensions import Annotated
import typer

sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="Append blocks to Notion page with chunking")


def parse_markdown_to_blocks(markdown_text):
    """Convert markdown text to Notion blocks."""
    blocks = []
    lines = markdown_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip empty lines but add dividers for multiple empties
        if not line.strip():
            i += 1
            continue

        # Horizontal rule (---)
        if line.strip() == '---':
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            i += 1
            continue

        # Heading 1 (#)
        if line.startswith('# ') and not line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                }
            })
            i += 1
            continue

        # Heading 2 (##)
        if line.startswith('## ') and not line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]
                }
            })
            i += 1
            continue

        # Heading 3 (###)
        if line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]
                }
            })
            i += 1
            continue

        # Bulleted list item (- or •)
        if line.startswith('- ') or line.startswith('• '):
            content = line[2:].strip()
            rich_text = parse_inline_formatting(content)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": rich_text
                }
            })
            i += 1
            continue

        # Numbered list item (1.)
        if re.match(r'^\d+\.\s', line):
            content = re.sub(r'^\d+\.\s', '', line)
            rich_text = parse_inline_formatting(content)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": rich_text
                }
            })
            i += 1
            continue

        # Quote (>)
        if line.startswith('> '):
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                }
            })
            i += 1
            continue

        # Code block (```)
        if line.startswith('```'):
            code_lines = []
            language = line[3:].strip() or 'plain text'
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1

            code_content = '\n'.join(code_lines)
            if code_content:
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": code_content}}],
                        "language": language
                    }
                })
            i += 1
            continue

        # Table detection (|...|)
        if '|' in line and line.strip().startswith('|'):
            # Skip for now - tables are complex in Notion
            i += 1
            continue

        # Regular paragraph
        rich_text = parse_inline_formatting(line)
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": rich_text
            }
        })
        i += 1

    return blocks


def parse_inline_formatting(text):
    """Parse inline formatting (bold, italic, code, links) into Notion rich_text."""
    # Simplified for now - just handle bold and basic text
    rich_text = []

    # Pattern to match **bold** and [citations]
    parts = re.split(r'(\*\*[^*]+\*\*|\[[^\]]+\])', text)

    for part in parts:
        if not part:
            continue

        if part.startswith('**') and part.endswith('**'):
            # Bold text
            content = part[2:-2]
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True}
            })
        elif part.startswith('[') and part.endswith(']'):
            # Citation - make it smaller/gray
            rich_text.append({
                "type": "text",
                "text": {"content": part},
                "annotations": {"color": "gray"}
            })
        else:
            # Regular text
            if part:
                rich_text.append({
                    "type": "text",
                    "text": {"content": part}
                })

    return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]


def chunk_blocks(blocks, max_chunk_size=100):
    """Split blocks into chunks that Notion can handle."""
    chunks = []
    current_chunk = []

    for block in blocks:
        current_chunk.append(block)
        if len(current_chunk) >= max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = []

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


@app.command()
def main(
    page_id: Annotated[str, typer.Option(help="Page ID")],
    markdown_file: Annotated[str, typer.Option(help="Path to markdown file")],
    image: Annotated[str, typer.Option(help="Path to image file to add at top")] = None,
    replace: Annotated[bool, typer.Option(help="Replace existing content")] = False,
):
    try:
        client = NotionClient()
        page_id = page_id.replace('-', '')

        # Delete existing blocks if --replace
        if replace:
            print("🗑️  Replacing existing content...")
            blocks_data = client.get_page_blocks(page_id)
            existing_blocks = blocks_data.get('results', [])

            if existing_blocks:
                print(f"   Deleting {len(existing_blocks)} existing blocks...")
                import requests
                for block in existing_blocks:
                    block_id = block['id'].replace('-', '')
                    url = f"https://api.notion.com/v1/blocks/{block_id}"
                    response = requests.delete(url, headers=client.headers)

        # Read markdown file
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Parse to blocks
        blocks = parse_markdown_to_blocks(markdown_content)

        if not blocks:
            print("❌ No content to append.")
            raise typer.Exit(1)

        # Add image at the top if provided
        if image:
            print(f"🖼️  Adding image from: {image}")
            # Notion doesn't support direct image upload via API easily
            # Instead, add a callout mentioning the image
            blocks.insert(0, {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"📊 Illustration available at: {image}"}
                    }],
                    "icon": {"type": "emoji", "emoji": "🖼️"},
                    "color": "blue_background"
                }
            })

        # Chunk the blocks
        chunks = chunk_blocks(blocks, max_chunk_size=95)

        print(f"📝 Uploading {len(blocks)} blocks in {len(chunks)} chunk(s)...")

        # Upload chunks sequentially
        for i, chunk in enumerate(chunks, 1):
            print(f"   Chunk {i}/{len(chunks)}: {len(chunk)} blocks...")
            client.append_blocks(page_id, chunk)

        print(f"\n✓ All blocks uploaded successfully!")
        print(f"   Total blocks: {len(blocks)}")
        print(f"   View at: https://www.notion.so/{page_id}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
