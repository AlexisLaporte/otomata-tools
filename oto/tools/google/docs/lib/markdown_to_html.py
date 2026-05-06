"""Convert markdown to standalone HTML for Google Drive import.

When uploaded with mimeType=application/vnd.google-apps.document, Drive converts
the HTML into a native Google Doc. This handles tables, links, code blocks,
nested lists, images, blockquotes natively — no manual Docs API indexing needed.

Style follows the .otomata/ convention (same as secrets.env): per-project file
in `.otomata/google-docs-style.css` (CWD or parents) overrides the user-level
file at `~/.otomata/google-docs-style.css`. No style is hardcoded — if neither
file exists, the doc is uploaded without a `<style>` block and Drive renders
it with its native defaults.
"""

import re
from pathlib import Path

import markdown as _md


STYLE_FILENAME = 'google-docs-style.css'


_EXTENSIONS = [
    'tables',
    'fenced_code',
    'sane_lists',
    'attr_list',
    'footnotes',
    'toc',
]

_LIST_LINE = re.compile(r'^\s*([-*+]|\d+[.)])\s+')


def find_docs_style() -> str:
    """Resolve CSS via the .otomata/ convention.

    Search order:
        1. `.otomata/google-docs-style.css` in CWD and up to 4 parent dirs
        2. `~/.otomata/google-docs-style.css`

    Returns the CSS content, or '' if no file is found.
    """
    cwd = Path.cwd()
    for _ in range(5):
        candidate = cwd / '.otomata' / STYLE_FILENAME
        if candidate.exists():
            return candidate.read_text(encoding='utf-8')
        if cwd.parent == cwd:
            break
        cwd = cwd.parent

    user_file = Path.home() / '.otomata' / STYLE_FILENAME
    if user_file.exists():
        return user_file.read_text(encoding='utf-8')

    return ''


def markdown_to_html(text: str, title: str = '', css: str = None) -> str:
    """Render markdown to a complete HTML document accepted by Drive's importer.

    Pass `css=None` to auto-resolve via the .otomata/ convention; pass a CSS
    string to override; pass `''` to skip the `<style>` block entirely.
    """
    body = _md.markdown(_normalize_lists(text), extensions=_EXTENSIONS, output_format='html')
    title_tag = f'<title>{_escape(title)}</title>' if title else ''
    if css is None:
        css = find_docs_style()
    style_tag = f'<style>{css}</style>' if css else ''
    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="utf-8">'
        f'{title_tag}{style_tag}'
        '</head><body>'
        f'{body}'
        '</body></html>'
    )


def _normalize_lists(text: str) -> str:
    """Insert a blank line before a list block when missing.

    Python-Markdown follows CommonMark and won't recognise a list that directly
    follows a paragraph line. GFM / most authors expect it to work — so we
    insert the blank line ourselves.
    """
    lines = text.split('\n')
    out: list[str] = []
    for line in lines:
        if _LIST_LINE.match(line) and out:
            prev = out[-1]
            if prev.strip() and not _LIST_LINE.match(prev):
                out.append('')
        out.append(line)
    return '\n'.join(out)


def _escape(s: str) -> str:
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;'))
