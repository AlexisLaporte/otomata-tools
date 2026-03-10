"""Google Keep client using gkeepapi (unofficial API)."""

from typing import Optional

import gkeepapi
from gkeepapi.node import ColorValue

from oto.config import get_secret, get_config_dir


class KeepClientError(Exception):
    """Google Keep client error."""


def _load_credentials() -> tuple[str, str]:
    """Load Keep credentials from otomata config.

    Returns (email, master_token).
    """
    email = get_secret('GOOGLE_KEEP_EMAIL')
    token = get_secret('GOOGLE_KEEP_MASTER_TOKEN')
    if not email or not token:
        raise KeepClientError(
            "Google Keep credentials not configured.\n"
            "Set GOOGLE_KEEP_EMAIL and GOOGLE_KEEP_MASTER_TOKEN in ~/.otomata/secrets.env\n"
            "Get a master token: pip install gpsoauth && python -c \"\n"
            "from gpsoauth import perform_master_login; "
            "print(perform_master_login('email', 'password', 'asdflkjh')['Token'])\""
        )
    return email, token


class KeepClient:
    """Google Keep client.

    Uses gkeepapi (unofficial) with master token auth.
    State is cached locally for faster subsequent syncs.

    Args:
        email: Google account email. If None, loaded from config.
        master_token: Master token. If None, loaded from config.
    """

    def __init__(
        self,
        email: Optional[str] = None,
        master_token: Optional[str] = None,
    ):
        if email is None or master_token is None:
            cfg_email, cfg_token = _load_credentials()
            email = email or cfg_email
            master_token = master_token or cfg_token

        self._email = email
        self._master_token = master_token
        self._keep = gkeepapi.Keep()
        self._synced = False

    def _ensure_synced(self):
        """Authenticate and sync if not already done."""
        if self._synced:
            return
        state = self._load_state()
        self._keep.authenticate(self._email, self._master_token, state=state)
        self._keep.sync()
        self._save_state()
        self._synced = True

    def _state_path(self):
        return get_config_dir() / 'google-keep-state.json'

    def _load_state(self) -> Optional[dict]:
        import json
        path = self._state_path()
        if path.exists():
            return json.loads(path.read_text())
        return None

    def _save_state(self):
        import json
        path = self._state_path()
        path.write_text(json.dumps(self._keep.dump()))

    def list_notes(
        self,
        query: Optional[str] = None,
        pinned: Optional[bool] = None,
        archived: bool = False,
        trashed: bool = False,
        labels: Optional[list[str]] = None,
        colors: Optional[list[str]] = None,
        max_results: int = 50,
    ) -> list[dict]:
        """List notes with optional filters.

        Args:
            query: Text search in title/body.
            pinned: Filter by pinned status.
            archived: Include archived notes.
            trashed: Include trashed notes.
            labels: Filter by label names.
            colors: Filter by color names (e.g. 'Red', 'Blue').
            max_results: Max notes to return.
        """
        self._ensure_synced()

        kwargs = {}
        if query:
            kwargs['query'] = query
        if pinned is not None:
            kwargs['pinned'] = pinned
        if archived:
            kwargs['archived'] = True
        if trashed:
            kwargs['trashed'] = True
        if labels:
            label_objs = []
            for name in labels:
                label = self._keep.findLabel(name)
                if label:
                    label_objs.append(label)
            if label_objs:
                kwargs['labels'] = label_objs
        if colors:
            kwargs['colors'] = [ColorValue[c] for c in colors]

        notes = list(self._keep.find(**kwargs))[:max_results]
        return [self._note_to_dict(n) for n in notes]

    def get_note(self, note_id: str) -> dict:
        """Get a note by ID."""
        self._ensure_synced()
        note = self._keep.get(note_id)
        if note is None:
            raise KeepClientError(f"Note not found: {note_id}")
        return self._note_to_dict(note, full=True)

    def create_note(
        self,
        title: str,
        text: str = '',
        pinned: bool = False,
        color: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict:
        """Create a text note."""
        self._ensure_synced()
        note = self._keep.createNote(title, text)
        note.pinned = pinned
        if color:
            note.color = ColorValue[color]
        if labels:
            for name in labels:
                label = self._keep.findLabel(name)
                if label is None:
                    label = self._keep.createLabel(name)
                note.labels.add(label)
        self._keep.sync()
        self._save_state()
        return self._note_to_dict(note)

    def create_list(
        self,
        title: str,
        items: list[tuple[str, bool]],
        pinned: bool = False,
        color: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict:
        """Create a checklist note.

        Args:
            title: List title.
            items: List of (text, checked) tuples.
        """
        self._ensure_synced()
        note = self._keep.createList(title, items)
        note.pinned = pinned
        if color:
            note.color = ColorValue[color]
        if labels:
            for name in labels:
                label = self._keep.findLabel(name)
                if label is None:
                    label = self._keep.createLabel(name)
                note.labels.add(label)
        self._keep.sync()
        self._save_state()
        return self._note_to_dict(note)

    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        text: Optional[str] = None,
        pinned: Optional[bool] = None,
        color: Optional[str] = None,
        archived: Optional[bool] = None,
    ) -> dict:
        """Update an existing note."""
        self._ensure_synced()
        note = self._keep.get(note_id)
        if note is None:
            raise KeepClientError(f"Note not found: {note_id}")

        if title is not None:
            note.title = title
        if text is not None:
            note.text = text
        if pinned is not None:
            note.pinned = pinned
        if color is not None:
            note.color = ColorValue[color]
        if archived is not None:
            if archived:
                note.archived = True
            else:
                note.archived = False

        self._keep.sync()
        self._save_state()
        return self._note_to_dict(note)

    def delete_note(self, note_id: str) -> dict:
        """Trash a note."""
        self._ensure_synced()
        note = self._keep.get(note_id)
        if note is None:
            raise KeepClientError(f"Note not found: {note_id}")
        note.trash()
        self._keep.sync()
        self._save_state()
        return {'id': note.id, 'status': 'trashed'}

    def list_labels(self) -> list[dict]:
        """List all labels."""
        self._ensure_synced()
        return [{'id': l.id, 'name': l.name} for l in self._keep.labels()]

    def _note_to_dict(self, note, full: bool = False) -> dict:
        """Convert a gkeepapi note to a dict."""
        is_list = hasattr(note, 'items')

        result = {
            'id': note.id,
            'title': note.title,
            'type': 'list' if is_list else 'note',
            'pinned': note.pinned,
            'archived': note.archived,
            'color': note.color.name if note.color else None,
            'labels': [l.name for l in note.labels.all()],
        }

        if is_list:
            result['items'] = [
                {'text': i.text, 'checked': i.checked}
                for i in note.items
            ]
        else:
            text = note.text
            if not full and len(text) > 200:
                text = text[:200] + '...'
            result['text'] = text

        if full:
            ts = note.timestamps
            result['timestamps'] = {
                'created': str(ts.created),
                'updated': str(ts.updated),
            }
            result['collaborators'] = list(note.collaborators.all())

        return result
