"""
Figma API Client.

Requires: requests
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret, get_cache_dir


class FigmaClient:
    """
    Figma REST API client with caching for:
    - File structure retrieval
    - Image export
    - Comments management
    - FigJam content extraction
    """

    BASE_URL = "https://api.figma.com/v1"

    def __init__(self, token: str = None, cache_ttl: int = 3600):
        """
        Initialize Figma client.

        Args:
            token: Figma API token (or set FIGMA_API_KEY env var)
            cache_ttl: Cache TTL in seconds (default 1 hour)
        """
        self.token = token or require_secret("FIGMA_API_KEY")
        self.headers = {
            "X-Figma-Token": self.token,
            "Content-Type": "application/json"
        }
        self.cache_dir = get_cache_dir() / "figma"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl

    def _cache_key(self, method: str, endpoint: str, params: Dict = None) -> str:
        """Generate cache key."""
        cache_data = {"method": method, "endpoint": endpoint, "params": params or {}}
        return hashlib.sha256(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[Dict]:
        """Get cached response."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        if time.time() - cache_file.stat().st_mtime > self.cache_ttl:
            cache_file.unlink()
            return None
        try:
            return json.loads(cache_file.read_text())
        except:
            return None

    def _set_cache(self, cache_key: str, data: Dict):
        """Set cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            pass

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
        use_cache: bool = True,
    ) -> Dict:
        """Make API request."""
        if use_cache and method == "GET":
            cache_key = self._cache_key(method, endpoint, params)
            cached = self._get_cached(cache_key)
            if cached:
                return cached

        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            json=data
        )
        response.raise_for_status()
        result = response.json()

        if use_cache and method == "GET":
            cache_key = self._cache_key(method, endpoint, params)
            self._set_cache(cache_key, result)

        return result

    # === FILE ENDPOINTS ===

    def get_file(
        self,
        file_key: str,
        depth: int = None,
        node_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Figma/FigJam file structure.

        Args:
            file_key: Figma file key
            depth: Tree depth limit
            node_ids: Specific node IDs to fetch

        Returns:
            File structure
        """
        params = {}
        if depth:
            params["depth"] = depth
        if node_ids:
            params["ids"] = ",".join(node_ids)

        return self._request("GET", f"files/{file_key}", params=params or None)

    def get_file_nodes(
        self,
        file_key: str,
        node_ids: List[str],
        depth: int = None,
    ) -> Dict[str, Any]:
        """Get specific nodes from a file."""
        params = {"ids": ",".join(node_ids)}
        if depth:
            params["depth"] = depth
        return self._request("GET", f"files/{file_key}/nodes", params=params)

    def get_file_meta(self, file_key: str) -> Dict[str, Any]:
        """Get file metadata only."""
        return self._request("GET", f"files/{file_key}/meta")

    # === IMAGE ENDPOINTS ===

    def get_images(
        self,
        file_key: str,
        node_ids: List[str],
        format: str = "png",
        scale: float = 2,
    ) -> Dict[str, Any]:
        """
        Export images from nodes.

        Args:
            file_key: Figma file key
            node_ids: Node IDs to export
            format: Image format (png, jpg, svg, pdf)
            scale: Scale factor

        Returns:
            Dict with image URLs
        """
        params = {
            "ids": ",".join(node_ids),
            "format": format,
            "scale": scale
        }
        return self._request("GET", f"images/{file_key}", params=params)

    def get_image_fills(self, file_key: str) -> Dict[str, Any]:
        """Get URLs for all images used as fills."""
        return self._request("GET", f"files/{file_key}/images")

    # === COMMENT ENDPOINTS ===

    def get_comments(self, file_key: str, as_markdown: bool = False) -> Dict[str, Any]:
        """Get all comments on a file."""
        params = {}
        if as_markdown:
            params["as_md"] = "true"
        return self._request("GET", f"files/{file_key}/comments", params=params or None)

    def post_comment(
        self,
        file_key: str,
        message: str,
        client_meta: Dict = None,
        comment_id: str = None,
    ) -> Dict[str, Any]:
        """
        Post a comment on a file.

        Args:
            file_key: Figma file key
            message: Comment text
            client_meta: Position data
            comment_id: Reply to comment ID

        Returns:
            Created comment
        """
        data = {"message": message}
        if comment_id:
            data["comment_id"] = comment_id
        if client_meta:
            data["client_meta"] = client_meta
        return self._request("POST", f"files/{file_key}/comments", data=data, use_cache=False)

    def delete_comment(self, file_key: str, comment_id: str) -> Dict[str, Any]:
        """Delete a comment."""
        return self._request("DELETE", f"files/{file_key}/comments/{comment_id}", use_cache=False)

    # === HELPER METHODS ===

    def find_nodes_by_type(self, document: Dict, node_type: str) -> List[Dict]:
        """Recursively find all nodes of a given type."""
        results = []

        def traverse(node):
            if node.get("type") == node_type:
                results.append(node)
            for child in node.get("children", []):
                traverse(child)

        traverse(document)
        return results

    def extract_stickies(self, document: Dict) -> List[Dict]:
        """Extract all sticky notes from a FigJam document."""
        stickies = self.find_nodes_by_type(document, "STICKY")
        return [{
            "id": s.get("id"),
            "text": s.get("characters", ""),
            "color": s.get("fills", [{}])[0].get("color") if s.get("fills") else None,
            "position": {
                "x": s.get("absoluteBoundingBox", {}).get("x"),
                "y": s.get("absoluteBoundingBox", {}).get("y")
            }
        } for s in stickies]

    def extract_connectors(self, document: Dict) -> List[Dict]:
        """Extract all connectors from a FigJam document."""
        connectors = self.find_nodes_by_type(document, "CONNECTOR")
        return [{
            "id": c.get("id"),
            "start_node": c.get("connectorStart", {}).get("endpointNodeId"),
            "end_node": c.get("connectorEnd", {}).get("endpointNodeId"),
            "text": c.get("characters", "")
        } for c in connectors]
