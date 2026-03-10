"""
Smart content filling for Google Slides based on layout strategies
"""
import re


def convert_markdown_to_text(content):
    """
    Advanced markdown to plain text conversion with formatting metadata

    Detects and preserves:
    - Bold (**text** or __text__)
    - Italic (*text* or _text_)
    - Links ([text](url))
    - Highlight (==text==)
    - Color (*{color:red}text*)
    - Bulleted lists (-, *)
    - Numbered lists (1., 2., 3.)
    - Nested lists (indentation with spaces/tabs)

    Returns:
        dict: {
            'text': str - Final text without markdown syntax
            'formatting': list - List of {type, start, end, value} dicts
            'list_items': list - List of {line_idx, is_numbered, nesting_level} dicts
        }
    """
    if not content:
        return {'text': '', 'formatting': [], 'list_items': []}

    # Remove images (handled separately)
    text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', '', content)

    # Remove headers but keep the text
    text = text.replace('###', '').replace('##', '').replace('#', '')

    lines = []
    line_formatting_list = []  # Store formatting per line
    list_items = []
    line_idx = 0

    for raw_line in text.split('\n'):
        # Detect nesting level (count leading spaces/tabs)
        nesting_level = 0
        stripped_line = raw_line.lstrip()
        indent = len(raw_line) - len(stripped_line)

        # 2 spaces or 1 tab = 1 nesting level
        if '\t' in raw_line[:indent]:
            nesting_level = raw_line[:indent].count('\t')
        else:
            nesting_level = indent // 2

        if not stripped_line:
            continue

        # Detect list items
        is_list = False
        is_numbered = False
        list_content = stripped_line

        # Numbered list (1. 2. 3. etc)
        numbered_match = re.match(r'^(\d+)\.\s+(.+)$', stripped_line)
        if numbered_match:
            is_list = True
            is_numbered = True
            list_content = numbered_match.group(2)

        # Bulleted list (- or *)
        elif stripped_line.startswith('- ') or stripped_line.startswith('* '):
            is_list = True
            is_numbered = False
            list_content = stripped_line[2:]

        line_text = list_content if is_list else stripped_line

        # Parse inline formatting (positions are relative to line start = 0)
        parsed_line, line_formatting = _parse_inline_formatting(line_text, 0)

        # Add tabs for nesting
        if nesting_level > 0:
            tabs = '\t' * nesting_level
            parsed_line = tabs + parsed_line
            # Adjust formatting positions for tabs
            tab_offset = len(tabs)
            for fmt in line_formatting:
                fmt['start'] += tab_offset
                fmt['end'] += tab_offset

        lines.append(parsed_line)
        line_formatting_list.append(line_formatting)

        if is_list:
            list_items.append({
                'line_idx': line_idx,
                'is_numbered': is_numbered,
                'nesting_level': nesting_level
            })

        line_idx += 1

    # Join lines and recalculate absolute positions
    final_text = '\n'.join(lines)

    # Recalculate formatting positions based on actual text
    formatting = []
    current_pos = 0

    for idx, (line, line_fmts) in enumerate(zip(lines, line_formatting_list)):
        for fmt in line_fmts:
            # Adjust positions relative to current line position in final text
            abs_fmt = {
                'type': fmt['type'],
                'start': current_pos + fmt['start'],
                'end': current_pos + fmt['end'],
                'value': fmt['value']
            }
            formatting.append(abs_fmt)

        # Move to next line: add line length + 1 for newline (except for last line)
        current_pos += len(line)
        if idx < len(lines) - 1:  # Not the last line
            current_pos += 1  # Add newline

    return {
        'text': final_text,
        'formatting': formatting,
        'list_items': list_items
    }


def _parse_inline_formatting(line, line_start_pos):
    """
    Parse inline formatting (bold, italic, links, highlight, colors) from a line

    Returns:
        tuple: (cleaned_text, formatting_list)
    """
    formatting = []
    replacements = []  # (start, end, replacement_text, formatting_info)

    # Find all patterns and collect them
    # 1. Links [text](url)
    for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', line):
        text = match.group(1)
        url = match.group(2)
        replacements.append((match.start(), match.end(), text, {
            'type': 'link',
            'value': url
        }))

    # 2. Highlight ==text==
    for match in re.finditer(r'==([^=]+)==', line):
        text = match.group(1)
        replacements.append((match.start(), match.end(), text, {
            'type': 'highlight',
            'value': '#FFFF00'
        }))

    # 3. Bold **text** or __text__
    for match in re.finditer(r'\*\*([^\*]+)\*\*|__([^_]+)__', line):
        text = match.group(1) or match.group(2)
        replacements.append((match.start(), match.end(), text, {
            'type': 'bold',
            'value': True
        }))

    # 4. Italic *text* or _text_ (single, not part of bold)
    for match in re.finditer(r'(?<!\*)\*([^\*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)', line):
        text = match.group(1) or match.group(2)
        replacements.append((match.start(), match.end(), text, {
            'type': 'italic',
            'value': True
        }))

    # Sort replacements by position (descending) to process from end to start
    replacements.sort(key=lambda x: x[0], reverse=True)

    # Apply replacements from end to start (so positions don't shift)
    result = line
    for old_start, old_end, new_text, fmt_info in replacements:
        # Calculate position in result text
        result = result[:old_start] + new_text + result[old_end:]

    # Now recalculate positions for formatting after all replacements
    replacements.sort(key=lambda x: x[0])  # Sort forward for position calculation
    offset = 0

    for old_start, old_end, new_text, fmt_info in replacements:
        # Position in final text
        new_start = old_start - offset
        new_end = new_start + len(new_text)

        formatting.append({
            'type': fmt_info['type'],
            'start': line_start_pos + new_start,
            'end': line_start_pos + new_end,
            'value': fmt_info['value']
        })

        # Update offset for next replacement
        offset += (old_end - old_start) - len(new_text)

    return result, formatting


class ContentFiller:
    """Smart content filling based on layout strategy"""

    def __init__(self, client, presentation_id):
        """
        Initialize ContentFiller

        Args:
            client: SlidesClient instance
            presentation_id: Google Slides presentation ID
        """
        self.client = client
        self.presentation_id = presentation_id

    def fill_slide(self, slide_id, yaml_layout, slide_data):
        """
        Fill slide based on its layout strategy

        Args:
            slide_id: Google Slides object ID
            yaml_layout: Layout name from YAML ('2-columns', 'default', etc.)
            slide_data: Dict with 'title', 'content', 'columns', etc.
        """
        from .layout_mappings import get_fill_strategy

        strategy_info = get_fill_strategy(yaml_layout)

        if not strategy_info:
            # Fallback to generic fill for layouts without strategy
            return self._fill_generic(slide_id, slide_data)

        strategy = strategy_info.get('strategy', 'title_and_body')

        if strategy == 'title_only':
            return self._fill_title_only(slide_id, slide_data)
        elif strategy == 'title_and_columns':
            return self._fill_title_and_columns(slide_id, slide_data)
        elif strategy == 'title_and_body':
            return self._fill_title_and_body(slide_id, slide_data)
        elif strategy == 'blank':
            return  # No text to fill for blank slides
        else:
            return self._fill_generic(slide_id, slide_data)

    def _get_slide(self, presentation, slide_id):
        """Get slide object from presentation by ID"""
        for slide in presentation.get('slides', []):
            if slide['objectId'] == slide_id:
                return slide
        return None

    def _get_placeholders_by_type(self, slide):
        """
        Extract placeholders grouped by type

        Returns:
            dict: {placeholder_type: [object_ids]}
        """
        placeholders = {}
        for element in slide.get('pageElements', []):
            shape = element.get('shape', {})
            placeholder = shape.get('placeholder', {})
            if placeholder:
                ptype = placeholder.get('type')
                if ptype not in placeholders:
                    placeholders[ptype] = []
                placeholders[ptype].append(element['objectId'])
        return placeholders

    def _insert_text_request(self, object_id, text):
        """Create insertText request"""
        return {
            'insertText': {
                'objectId': object_id,
                'text': text,
                'insertionIndex': 0
            }
        }

    def _apply_formatting(self, object_id, formatting_list):
        """
        Apply text formatting (bold, italic, links, colors) to a text object

        Args:
            object_id: Text box object ID
            formatting_list: List of formatting dicts from convert_markdown_to_text
        """
        if not formatting_list:
            return

        for fmt in formatting_list:
            fmt_type = fmt['type']
            start = fmt['start']
            end = fmt['end']
            value = fmt['value']

            if fmt_type == 'bold':
                self.client.format_text_range(
                    self.presentation_id, object_id, start, end, bold=True
                )
            elif fmt_type == 'italic':
                self.client.format_text_range(
                    self.presentation_id, object_id, start, end, italic=True
                )
            elif fmt_type == 'link':
                self.client.format_text_range(
                    self.presentation_id, object_id, start, end, link=value
                )
            elif fmt_type == 'highlight':
                self.client.format_text_range(
                    self.presentation_id, object_id, start, end, bg_color=value
                )

    def _create_bullets_requests(self, object_id, text, list_items):
        """
        Create bullet/numbered list formatting requests

        Args:
            object_id: Text box object ID
            text: The full text content
            list_items: List of dicts with {line_idx, is_numbered, nesting_level}

        Returns:
            list: List of createParagraphBullets requests
        """
        if not list_items:
            return []

        # Check if all list items are the same type (all bulleted or all numbered)
        all_numbered = all(item['is_numbered'] for item in list_items)
        all_bulleted = all(not item['is_numbered'] for item in list_items)

        # If all items are the same type, apply bullets to all text at once
        if all_numbered or all_bulleted:
            bullet_preset = 'NUMBERED_DIGIT_ALPHA_ROMAN' if all_numbered else 'BULLET_DISC_CIRCLE_SQUARE'
            return [{
                'createParagraphBullets': {
                    'objectId': object_id,
                    'textRange': {'type': 'ALL'},
                    'bulletPreset': bullet_preset
                }
            }]

        # Mixed types: need to apply bullets line by line
        requests = []
        lines = text.split('\n')
        current_pos = 0
        list_items_by_line = {item['line_idx']: item for item in list_items}

        for line_idx, line in enumerate(lines):
            line_length = len(line)

            if line_idx in list_items_by_line and line_length > 0:
                item = list_items_by_line[line_idx]
                is_numbered = item['is_numbered']
                bullet_preset = 'NUMBERED_DIGIT_ALPHA_ROMAN' if is_numbered else 'BULLET_DISC_CIRCLE_SQUARE'

                # Calculate end - be conservative, don't include trailing newline
                end_index = current_pos + line_length

                requests.append({
                    'createParagraphBullets': {
                        'objectId': object_id,
                        'textRange': {
                            'type': 'FIXED_RANGE',
                            'startIndex': current_pos,
                            'endIndex': end_index
                        },
                        'bulletPreset': bullet_preset
                    }
                })

            current_pos += line_length + 1  # +1 for newline character

        return requests

    def _execute_requests(self, requests):
        """Execute batch update requests"""
        if requests:
            self.client.slides_service.presentations().batchUpdate(
                presentationId=self.presentation_id,
                body={'requests': requests}
            ).execute()

    def _fill_title_only(self, slide_id, slide_data):
        """
        Fill title placeholder only (for hero, title-slide layouts)

        Args:
            slide_id: Slide object ID
            slide_data: Dict with 'title', 'content'
        """
        presentation = self.client.get_presentation(self.presentation_id)
        slide = self._get_slide(presentation, slide_id)

        if not slide:
            return

        requests = []
        placeholders = self._get_placeholders_by_type(slide)

        # Fill title
        title = slide_data.get('title', '')
        if title and placeholders.get('TITLE'):
            requests.append(self._insert_text_request(
                placeholders['TITLE'][0],
                title
            ))

        # For title-slide, also fill subtitle with content
        content = slide_data.get('content', '')
        subtitle_id = None
        parsed_content = None

        if content and placeholders.get('SUBTITLE'):
            parsed_content = convert_markdown_to_text(content)
            if parsed_content['text']:
                subtitle_id = placeholders['SUBTITLE'][0]
                requests.append(self._insert_text_request(subtitle_id, parsed_content['text']))
                # Add bullet formatting after text insertion
                requests.extend(self._create_bullets_requests(subtitle_id, parsed_content['text'], parsed_content['list_items']))

        self._execute_requests(requests)

        # Apply formatting after text is inserted
        if subtitle_id and parsed_content and parsed_content['formatting']:
            self._apply_formatting(subtitle_id, parsed_content['formatting'])

    def _fill_title_and_body(self, slide_id, slide_data):
        """
        Fill title and body placeholders (for default, section, toc, thanks, numbers layouts)

        Args:
            slide_id: Slide object ID
            slide_data: Dict with 'title', 'content'
        """
        presentation = self.client.get_presentation(self.presentation_id)
        slide = self._get_slide(presentation, slide_id)

        if not slide:
            return

        requests = []
        placeholders = self._get_placeholders_by_type(slide)

        # Fill title
        title = slide_data.get('title', '')
        if title and placeholders.get('TITLE'):
            requests.append(self._insert_text_request(
                placeholders['TITLE'][0],
                title
            ))

        # Fill body
        content = slide_data.get('content', '')
        body_id = None
        parsed_content = None

        if content and placeholders.get('BODY'):
            parsed_content = convert_markdown_to_text(content)
            if parsed_content['text']:
                body_id = placeholders['BODY'][0]
                requests.append(self._insert_text_request(body_id, parsed_content['text']))
                # Add bullet formatting after text insertion
                requests.extend(self._create_bullets_requests(body_id, parsed_content['text'], parsed_content['list_items']))

        self._execute_requests(requests)

        # Apply formatting after text is inserted
        if body_id and parsed_content and parsed_content['formatting']:
            self._apply_formatting(body_id, parsed_content['formatting'])

    def _fill_title_and_columns(self, slide_id, slide_data):
        """
        Fill title and column placeholders (for 2-columns, 3-columns layouts)

        Args:
            slide_id: Slide object ID
            slide_data: Dict with 'title', 'columns' (list of dicts with 'content')
        """
        presentation = self.client.get_presentation(self.presentation_id)
        slide = self._get_slide(presentation, slide_id)

        if not slide:
            return

        requests = []
        placeholders = self._get_placeholders_by_type(slide)

        # Fill title
        title = slide_data.get('title', '')
        if title and placeholders.get('TITLE'):
            requests.append(self._insert_text_request(
                placeholders['TITLE'][0],
                title
            ))

        # Fill columns into SUBTITLE placeholders
        columns = slide_data.get('columns', [])
        subtitle_placeholders = placeholders.get('SUBTITLE', [])
        parsed_columns = []

        for i, col in enumerate(columns):
            if i < len(subtitle_placeholders):
                parsed = convert_markdown_to_text(col.get('content', ''))
                if parsed['text']:
                    subtitle_id = subtitle_placeholders[i]
                    requests.append(self._insert_text_request(subtitle_id, parsed['text']))
                    # Add bullet formatting after text insertion
                    requests.extend(self._create_bullets_requests(subtitle_id, parsed['text'], parsed['list_items']))
                    parsed_columns.append((subtitle_id, parsed))

        self._execute_requests(requests)

        # Apply formatting after text is inserted
        for subtitle_id, parsed in parsed_columns:
            if parsed['formatting']:
                self._apply_formatting(subtitle_id, parsed['formatting'])

    def _fill_generic(self, slide_id, slide_data):
        """
        Generic fallback: fill title and first content placeholder

        Args:
            slide_id: Slide object ID
            slide_data: Dict with 'title', 'content'
        """
        presentation = self.client.get_presentation(self.presentation_id)
        slide = self._get_slide(presentation, slide_id)

        if not slide:
            return

        requests = []

        # Find and fill placeholders
        for element in slide.get('pageElements', []):
            shape = element.get('shape', {})
            placeholder = shape.get('placeholder', {})

            if not placeholder:
                continue

            placeholder_type = placeholder.get('type', '')
            object_id = element['objectId']

            # Fill title
            if placeholder_type in ['TITLE', 'CENTERED_TITLE']:
                title = slide_data.get('title', '')
                if title:
                    requests.append(self._insert_text_request(object_id, title))

            # Fill body
            elif placeholder_type in ['BODY', 'SUBTITLE']:
                content = slide_data.get('content', '')
                if content:
                    parsed = convert_markdown_to_text(content)
                    if parsed['text']:
                        requests.append(self._insert_text_request(object_id, parsed['text']))
                        # Add bullet formatting after text insertion
                        requests.extend(self._create_bullets_requests(object_id, parsed['text'], parsed['list_items']))

                        self._execute_requests(requests)

                        # Apply formatting after text is inserted
                        if parsed['formatting']:
                            self._apply_formatting(object_id, parsed['formatting'])

                        break  # Only fill first content placeholder

        # Execute if there are pending requests (title only)
        if requests:
            self._execute_requests(requests)
