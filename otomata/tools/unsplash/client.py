"""
Unsplash API Client for stock photo search.

Requires: requests
"""

import time
from typing import Optional, Dict, Any, List, Union

import requests

from ...config import get_secret


class UnsplashClient:
    """
    Unsplash API client for:
    - Photo search
    - Random photos
    - Photo details
    """

    BASE_URL = "https://api.unsplash.com"

    def __init__(self, api_key: str = None):
        """
        Initialize Unsplash client.

        Args:
            api_key: Unsplash API access key (or set UNSPLASH_API_KEY env var)
        """
        self.api_key = api_key or get_secret("UNSPLASH_API_KEY")
        self.use_source_api = not self.api_key

        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Client-ID {self.api_key}",
                "Accept-Version": "v1"
            })

        self._last_request = 0.0
        self._min_interval = 0.5

    def _rate_limit(self):
        """Ensure minimum time between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _request(self, endpoint: str, params: Dict) -> Union[Dict, List]:
        """Make API request."""
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def search_photos(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        order_by: str = "relevant",
        color: str = None,
        orientation: str = None,
    ) -> Dict[str, Any]:
        """
        Search for photos.

        Args:
            query: Search query
            page: Page number
            per_page: Results per page (max 30)
            order_by: Sort order ('relevant' or 'latest')
            color: Color filter ('black_and_white', 'black', 'white', etc.)
            orientation: Orientation filter ('landscape', 'portrait', 'squarish')

        Returns:
            Search results with 'results' array
        """
        if self.use_source_api:
            return self._get_random_via_source(query, per_page, orientation)

        params = {
            "query": query,
            "page": page,
            "per_page": min(per_page, 30),
            "order_by": order_by
        }

        if color:
            params["color"] = color
        if orientation:
            params["orientation"] = orientation

        return self._request("/search/photos", params)

    def _get_random_via_source(
        self,
        query: str,
        count: int,
        orientation: str = None,
    ) -> Dict[str, Any]:
        """Get random images via Unsplash Source API (no auth required)."""
        import hashlib

        results = []
        for i in range(count):
            width = 1920 if orientation == "landscape" else 1080 if orientation == "portrait" else 1600
            height = 1080 if orientation == "landscape" else 1920 if orientation == "portrait" else 1600

            url = f"https://source.unsplash.com/random/{width}x{height}/?{query}"
            response = self.session.get(url, allow_redirects=True)
            final_url = response.url

            photo_id = hashlib.md5(final_url.encode()).hexdigest()[:11]
            if "/photo-" in final_url:
                photo_id = final_url.split("/photo-")[1].split("?")[0][:11]

            results.append({
                "id": photo_id,
                "description": f"Random image for '{query}'",
                "urls": {
                    "raw": final_url,
                    "full": final_url,
                    "regular": final_url,
                },
                "links": {
                    "html": f"https://unsplash.com/photos/{photo_id}",
                    "download": final_url
                },
                "user": {"name": "Unsplash", "username": "unsplash"},
                "width": width,
                "height": height,
            })
            time.sleep(0.3)

        return {"total": count, "total_pages": 1, "results": results}

    def get_photo(self, photo_id: str) -> Dict[str, Any]:
        """
        Get photo details.

        Args:
            photo_id: Unsplash photo ID

        Returns:
            Photo details
        """
        return self._request(f"/photos/{photo_id}", {})

    def get_random_photo(
        self,
        query: str = None,
        orientation: str = None,
        count: int = 1,
    ) -> Union[Dict, List[Dict]]:
        """
        Get random photo(s).

        Args:
            query: Optional search query
            orientation: Orientation filter
            count: Number of photos (max 30)

        Returns:
            Random photo(s)
        """
        params = {"count": min(count, 30)}
        if query:
            params["query"] = query
        if orientation:
            params["orientation"] = orientation

        return self._request("/photos/random", params)

    def download_photo(self, photo_id: str, download_location: str) -> Dict:
        """
        Trigger download event (required by Unsplash guidelines).

        Args:
            photo_id: Photo ID
            download_location: Download URL from photo object

        Returns:
            Download response
        """
        self._rate_limit()
        try:
            response = self.session.get(download_location)
            response.raise_for_status()
            return response.json()
        except:
            return {}
