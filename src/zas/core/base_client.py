"""Base API client with common functionality."""

from typing import Any, Dict, Optional
import time
import requests
from abc import ABC, abstractmethod

from .exceptions import APIException


class BaseAPIClient(ABC):
    """
    Abstract base class for API clients.
    
    Provides common functionality like:
    - Request handling with retries
    - Rate limiting
    - Error handling
    - Authentication
    """
    
    def __init__(
        self,
        base_url: str,
        auth: tuple[str, str],
        timeout: int = 20,
        rate_limit_delay: float = 0.15,
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            auth: Authentication tuple (username, password/token)
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between requests for rate limiting
        """
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path (will be appended to base_url)
            params: Query parameters
            json: JSON body
            data: Raw data body
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            APIException: If the request fails
        """
        self._rate_limit()
        
        url = f"{self.base_url}{path}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                auth=self.auth,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            raise APIException(
                f"HTTP {status_code} error: {str(e)}",
                status_code=status_code
            )
        except requests.exceptions.RequestException as e:
            raise APIException(f"Request failed: {str(e)}")
        except ValueError as e:
            raise APIException(f"Invalid JSON response: {str(e)}")
    
    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request("GET", path, params=params)
    
    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request("POST", path, json=json, data=data)
    
    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return self._make_request("PUT", path, json=json)
    
    def delete(
        self,
        path: str,
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self._make_request("DELETE", path)
