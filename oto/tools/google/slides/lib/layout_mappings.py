"""
Layout mappings for 321 template
Maps YAML layout names to Google Slides layout properties

SELECTION: 12 layouts essentiels uniquement (user-selected)
"""

# Complete mapping of 321 template layouts
# Based on template ID: 1rA2YmYTA5P2O7GHgv9p3JwouO0lVVZEpZyKFFUKiVH4

LAYOUT_321_MAPPINGS = {
    # YAML name → (index, API name, display name, usage, fill_strategy)

    # === 12 SELECTED LAYOUTS (with fill strategies) ===

    'title-slide': (0, 'TITLE', 'Title slide', 'Page de titre (première slide)', {
        'strategy': 'title_only',
        'placeholders': ['TITLE', 'SUBTITLE']
    }),
    'default': (2, 'TITLE_AND_BODY', 'Title and body', 'Slide standard avec titre + texte', {
        'strategy': 'title_and_body',
        'placeholders': ['TITLE', 'BODY']
    }),
    'hero': (6, 'MAIN_POINT', 'Main point', 'Grand titre impact', {
        'strategy': 'title_only',
        'placeholders': ['TITLE']
    }),
    '2-columns': (3, 'TITLE_AND_TWO_COLUMNS', 'Title and two columns', 'Titre + 2 colonnes', {
        'strategy': 'title_and_columns',
        'placeholders': ['TITLE', 'SUBTITLE', 'SUBTITLE'],
        'column_count': 2
    }),
    '3-columns': (24, 'CUSTOM_1', 'Title and three columns', 'Titre + 3 colonnes', {
        'strategy': 'title_and_columns',
        'placeholders': ['TITLE', 'SUBTITLE', 'SUBTITLE', 'SUBTITLE'],
        'column_count': 3
    }),
    'section': (20, 'CUSTOM_4_1_1_1_2', 'Title and text 3 1', 'Séparateur section (coloré)', {
        'strategy': 'title_and_body',
        'placeholders': ['TITLE', 'BODY']
    }),
    'section-alt': (17, 'CUSTOM_4_1', 'Title and text 1', 'Séparateur section (gris)', {
        'strategy': 'title_and_body',
        'placeholders': ['TITLE', 'BODY']
    }),
    'blank': (10, 'BLANK', 'Blank', 'Vierge pour grosse image/diagramme', {
        'strategy': 'blank',
        'placeholders': []
    }),
    'toc': (11, 'CUSTOM', 'Table of contents', 'Table des matières', {
        'strategy': 'title_and_body',
        'placeholders': ['TITLE', 'BODY']
    }),
    'thanks': (30, 'CUSTOM_2', 'Thanks', 'Page de remerciements', {
        'strategy': 'title_and_body',
        'placeholders': ['TITLE', 'BODY']
    }),
    'numbers': (28, 'CUSTOM_5', 'Numbers and text', '3 blocs numérotés', {
        'strategy': 'title_and_body',
        'placeholders': ['TITLE', 'BODY']
    }),
    'numbers-5': (29, 'CUSTOM_5_1', 'Numbers and text 1', '5 blocs numérotés', {
        'strategy': 'title_and_body',
        'placeholders': ['TITLE', 'BODY']
    }),

    # === OTHER LAYOUTS (no fill strategy, for reference only) ===

    'section-header': (1, 'SECTION_HEADER', 'Section header', None, None),
    'one-column': (5, 'ONE_COLUMN_TEXT', 'One column text', None, None),
    'section-desc': (7, 'SECTION_TITLE_AND_DESCRIPTION', 'Section title and description', None, None),
    'caption': (8, 'CAPTION_ONLY', 'Caption', None, None),
    'big-number': (9, 'BIG_NUMBER', 'Big number', None, None),
    'quote': (12, 'CUSTOM_3', 'Quote', None, None),
    'title-only-1': (13, 'CUSTOM_7', 'Title only 1', None, None),
    'title-only-2': (14, 'CUSTOM_7_1', 'Title only 2', None, None),
    'title-only-3': (15, 'CUSTOM_7_1_1', 'Title only 3', None, None),
    'title-text': (16, 'CUSTOM_4', 'Title and text', None, None),
    'title-text-2': (18, 'CUSTOM_4_1_1', 'Title and text 2', None, None),
    'title-text-3': (19, 'CUSTOM_4_1_1_1', 'Title and text 3', None, None),
    'title-text-4': (21, 'CUSTOM_4_1_1_1_1', 'Title and text 4', None, None),
    'title-text-5': (22, 'CUSTOM_4_1_1_1_1_1', 'Title and text 5', None, None),
    '2-columns-1': (23, 'CUSTOM_6', 'Title and two columns 1', None, None),
    '3-columns-1': (25, 'CUSTOM_1_2', 'Title and three columns 1', None, None),
    '4-columns': (26, 'CUSTOM_1_1', 'Title and four columns', None, None),
    '6-columns': (27, 'CUSTOM_1_1_1', 'Title and six columns', None, None),
    'background': (31, 'CUSTOM_8_1', 'Background', None, None),
    'background-1': (32, 'CUSTOM_8_1_1', 'Background 1', None, None),
    'blank-slide': (33, 'BLANK', 'Blank slide', None, None),
    'more': (34, 'CUSTOM', 'More', None, None),
}

# Reverse mapping: Display name → YAML name
DISPLAY_NAME_TO_YAML = {
    display_name: yaml_name
    for yaml_name, info in LAYOUT_321_MAPPINGS.items()
    if len(info) >= 3 and info[2]
    for display_name in [info[2]]
}

# API name mapping for lookup
API_NAME_TO_YAML = {
    api_name: yaml_name
    for yaml_name, info in LAYOUT_321_MAPPINGS.items()
    if len(info) >= 2 and info[1]
    for api_name in [info[1]]
}


def get_layout_info(yaml_layout_name):
    """
    Get layout information from YAML name

    Args:
        yaml_layout_name: YAML layout name (e.g., '3-columns')

    Returns:
        tuple: (index, api_name, display_name, usage, fill_strategy) or None if not found
    """
    return LAYOUT_321_MAPPINGS.get(yaml_layout_name)


def get_api_name(yaml_layout_name):
    """
    Get Google Slides API name from YAML layout name

    Args:
        yaml_layout_name: YAML layout name (e.g., '3-columns')

    Returns:
        str: API name (e.g., 'CUSTOM_1') or 'TITLE_AND_BODY' as fallback
    """
    info = LAYOUT_321_MAPPINGS.get(yaml_layout_name)
    if info and len(info) >= 2:
        return info[1]  # API name
    return 'TITLE_AND_BODY'  # Fallback


def get_display_name(yaml_layout_name):
    """
    Get display name from YAML layout name

    Args:
        yaml_layout_name: YAML layout name (e.g., '3-columns')

    Returns:
        str: Display name (e.g., 'Title and three columns')
    """
    info = LAYOUT_321_MAPPINGS.get(yaml_layout_name)
    if info and len(info) >= 3:
        return info[2]  # Display name
    return 'Title and body'  # Fallback


def get_fill_strategy(yaml_layout_name):
    """
    Get fill strategy dict for a layout

    Args:
        yaml_layout_name: YAML layout name (e.g., '3-columns')

    Returns:
        dict: Fill strategy with 'strategy', 'placeholders', etc. or None
    """
    info = LAYOUT_321_MAPPINGS.get(yaml_layout_name)
    if info and len(info) >= 5 and isinstance(info[4], dict):
        return info[4]
    return None


def get_all_layouts():
    """
    Get list of all available layouts with their descriptions

    Returns:
        list: List of tuples (yaml_name, display_name, usage)
    """
    return [
        (yaml_name, info[2], info[3] if len(info) > 3 else '')
        for yaml_name, info in LAYOUT_321_MAPPINGS.items()
        if len(info) >= 3 and info[2]
    ]
