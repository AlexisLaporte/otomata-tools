"""
Markdown to Notion blocks converter.

Supports:
- Headers (h1, h2, h3)
- Paragraphs with inline formatting (bold, italic, code, links)
- Bullet and numbered lists
- Code blocks
- Blockquotes
- Tables
- Horizontal rules
- Frontmatter stripping
"""
import re
from typing import List, Dict, Any


# Supported Notion code languages
NOTION_LANGUAGES = {
    'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'c++', 'csharp', 'c#',
    'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'sql', 'bash',
    'shell', 'powershell', 'html', 'css', 'json', 'yaml', 'xml', 'markdown',
    'plain text', 'plaintext'
}


def markdown_to_notion_blocks(markdown_content: str, max_blocks: int = 100) -> List[Dict[str, Any]]:
    """
    Convert markdown content to Notion blocks.

    Args:
        markdown_content: Raw markdown string
        max_blocks: Maximum number of blocks (Notion API limit is 100 per request)

    Returns:
        List of Notion block objects
    """
    # Strip frontmatter
    content = _strip_frontmatter(markdown_content)

    blocks = []
    lines = content.split('\n')
    i = 0

    while i < len(lines) and len(blocks) < max_blocks:
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', line.strip()):
            blocks.append({"type": "divider", "divider": {}})
            i += 1
            continue

        # Headers (check ### before ## before #)
        if line.startswith('### '):
            blocks.append({
                "type": "heading_3",
                "heading_3": {"rich_text": _parse_inline_formatting(line[4:].strip())}
            })
            i += 1
            continue

        if line.startswith('## '):
            blocks.append({
                "type": "heading_2",
                "heading_2": {"rich_text": _parse_inline_formatting(line[3:].strip())}
            })
            i += 1
            continue

        if line.startswith('# '):
            blocks.append({
                "type": "heading_1",
                "heading_1": {"rich_text": _parse_inline_formatting(line[2:].strip())}
            })
            i += 1
            continue

        # Code blocks
        if line.startswith('```'):
            language = line[3:].strip() or 'plain text'
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code_content = '\n'.join(code_lines)
            # Notion has 2000 char limit per block
            if len(code_content) > 2000:
                code_content = code_content[:1997] + '...'
            blocks.append({
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": code_content}}],
                    "language": language if language in NOTION_LANGUAGES else "plain text"
                }
            })
            i += 1
            continue

        # Tables - detect by | at start
        if line.strip().startswith('|') and '|' in line[1:]:
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_block = _parse_table(table_lines)
            if table_block:
                blocks.append(table_block)
            continue

        # Blockquotes
        if line.startswith('> '):
            blocks.append({
                "type": "quote",
                "quote": {"rich_text": _parse_inline_formatting(line[2:].strip())}
            })
            i += 1
            continue

        # Bullet lists
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            content = line.strip()[2:].strip()
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _parse_inline_formatting(content)}
            })
            i += 1
            continue

        # Numbered lists
        if re.match(r'^\d+\.\s', line.strip()):
            content = re.sub(r'^\d+\.\s', '', line.strip())
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": _parse_inline_formatting(content)}
            })
            i += 1
            continue

        # Regular paragraph
        content = line.strip()
        if content:
            if len(content) > 2000:
                content = content[:1997] + '...'
            blocks.append({
                "type": "paragraph",
                "paragraph": {"rich_text": _parse_inline_formatting(content)}
            })

        i += 1

    return blocks[:max_blocks]


def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown."""
    if content.startswith('---'):
        try:
            end = content.index('---', 3)
            return content[end + 3:].lstrip('\n')
        except ValueError:
            pass
    return content


def _parse_inline_formatting(text: str) -> List[Dict[str, Any]]:
    """
    Parse inline markdown formatting into Notion rich_text array.

    Supports: **bold**, *italic*, `code`, [links](url)
    """
    if not text:
        return [{"type": "text", "text": {"content": ""}}]

    rich_text = []

    # Combined pattern for all inline formatting
    # Order matters: bold before italic (** before *)
    pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))'

    parts = re.split(pattern, text)

    for part in parts:
        if not part:
            continue

        # Bold **text**
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            content = part[2:-2]
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True}
            })
        # Italic *text*
        elif part.startswith('*') and part.endswith('*') and len(part) > 2 and not part.startswith('**'):
            content = part[1:-1]
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"italic": True}
            })
        # Code `text`
        elif part.startswith('`') and part.endswith('`') and len(part) > 2:
            content = part[1:-1]
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"code": True}
            })
        # Link [text](url)
        elif part.startswith('[') and '](' in part and part.endswith(')'):
            match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', part)
            if match:
                link_text, url = match.groups()
                rich_text.append({
                    "type": "text",
                    "text": {"content": link_text, "link": {"url": url}}
                })
            else:
                rich_text.append({"type": "text", "text": {"content": part}})
        # Plain text
        else:
            rich_text.append({"type": "text", "text": {"content": part}})

    return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]


def _parse_table(table_lines: List[str]) -> Dict[str, Any]:
    """
    Parse markdown table into Notion table block.

    Notion tables have a specific structure with table_width and rows.
    """
    if len(table_lines) < 2:
        return None

    # Parse rows, skip separator line (contains only |, -, :, spaces)
    rows = []
    for line in table_lines:
        # Skip separator line
        if re.match(r'^[\s|:-]+$', line):
            continue

        # Parse cells
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells:
            rows.append(cells)

    if not rows:
        return None

    # Determine table width (max columns)
    table_width = max(len(row) for row in rows)

    # Build Notion table block
    table_rows = []
    for idx, row in enumerate(rows):
        # Pad row to table_width if needed
        while len(row) < table_width:
            row.append('')

        cells = []
        for cell_content in row:
            cells.append(_parse_inline_formatting(cell_content))

        table_rows.append({
            "type": "table_row",
            "table_row": {"cells": cells}
        })

    return {
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": True,  # First row is header
            "has_row_header": False,
            "children": table_rows
        }
    }
