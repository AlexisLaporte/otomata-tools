"""
Phantombuster API Client for automation agents.

Requires: requests
"""

import time
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret


class PhantombusterClient:
    """
    Phantombuster API client for:
    - Agent launch and management
    - Container monitoring
    - Results retrieval
    """

    BASE_URL = "https://api.phantombuster.com/api/v2"

    def __init__(self, api_key: str = None):
        """
        Initialize Phantombuster client.

        Args:
            api_key: Phantombuster API key (or set PHANTOMBUSTER_API_KEY env var)
        """
        self.api_key = api_key or require_secret("PHANTOMBUSTER_API_KEY")
        self._last_request = 0.0

    def _rate_limit(self):
        """Enforce minimum 1 second between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_request = time.time()

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"X-Phantombuster-Key": self.api_key}

        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def launch_agent(self, agent_id: str, config: Dict = None) -> Dict[str, Any]:
        """
        Launch an agent.

        Args:
            agent_id: Agent ID
            config: Agent configuration (argument, bonusArgument, etc.)

        Returns:
            Container info with containerId
        """
        data = {"id": agent_id}
        if config:
            data.update(config)

        return self._request("POST", "agents/launch", json=data)

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent details.

        Args:
            agent_id: Agent ID

        Returns:
            Agent configuration and status
        """
        return self._request("GET", f"agents/{agent_id}")

    def get_container(self, container_id: str) -> Dict[str, Any]:
        """
        Get container status.

        Args:
            container_id: Container ID

        Returns:
            Container status and metadata
        """
        return self._request("GET", f"containers/{container_id}")

    def get_container_results(self, container_id: str) -> Any:
        """
        Get parsed JSON results from container.

        Args:
            container_id: Container ID

        Returns:
            Parsed results
        """
        data = self.get_container(container_id)
        result_url = data.get("resultUrl")
        if result_url:
            response = requests.get(result_url)
            response.raise_for_status()
            return response.json()
        return None

    def get_container_output(self, container_id: str) -> str:
        """
        Get container output logs.

        Args:
            container_id: Container ID

        Returns:
            Output text
        """
        data = self.get_container(container_id)
        output_url = data.get("outputUrl")
        if output_url:
            response = requests.get(output_url)
            response.raise_for_status()
            return response.text
        return ""

    def list_containers(self, agent_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List containers.

        Args:
            agent_id: Filter by agent
            limit: Max results

        Returns:
            List of containers
        """
        params = {"limit": limit}
        if agent_id:
            params["agentId"] = agent_id

        return self._request("GET", "containers", params=params)

    def wait_for_container(
        self,
        container_id: str,
        max_wait: int = 300,
        check_interval: int = 10,
    ) -> Dict[str, Any]:
        """
        Wait for container to complete.

        Args:
            container_id: Container ID
            max_wait: Maximum wait time in seconds
            check_interval: Check interval in seconds

        Returns:
            Final container status

        Raises:
            TimeoutError: If container doesn't complete
        """
        start = time.time()
        while time.time() - start < max_wait:
            data = self.get_container(container_id)
            status = data.get("status")

            if status in ("finished", "error", "stopped"):
                return data

            time.sleep(check_interval)

        raise TimeoutError(f"Container {container_id} did not complete in {max_wait}s")
