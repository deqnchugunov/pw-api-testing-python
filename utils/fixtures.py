from typing import Dict, Any, Optional
from playwright.async_api import APIRequestContext
import asyncio
from utils.logger import logger


class APIClient:
    """API client with fluent interface as shown in screenshot"""
    
    def __init__(self, request: APIRequestContext):
        self.request = request
        self._path: str = ""
        self._params: Dict[str, Any] = {}
        self._body: Optional[Dict[str, Any]] = None
        self._headers: Dict[str, str] = {}
        self._expected_status: Optional[int] = None
    
    def path(self, url: str) -> 'APIClient':
        """Set API path"""
        self._path = url
        return self
    
    def params(self, params: Dict[str, Any]) -> 'APIClient':
        """Set query parameters"""
        self._params = params
        return self
    
    def body(self, data: Dict[str, Any]) -> 'APIClient':
        """Set request body"""
        self._body = data
        return self
    
    def headers(self, headers: Dict[str, str]) -> 'APIClient':
        """Set request headers"""
        self._headers = headers
        return self
    
    async def get_request(self, expected_status: int = 200) -> Any:
        """Make GET request"""
        self._expected_status = expected_status
        logger.info(f"GET {self._path}", extra={"params": self._params})
        
        response = await self.request.get(
            self._path,
            params=self._params,
            headers=self._headers
        )
        
        logger.info(f"GET {self._path} - Status: {response.status}")
        self._reset()
        return response
    
    async def post_request(self, expected_status: int = 201) -> Any:
        """Make POST request"""
        self._expected_status = expected_status
        logger.info(f"POST {self._path}", extra={"body": self._body})
        
        response = await self.request.post(
            self._path,
            data=self._body,
            headers=self._headers
        )
        
        logger.info(f"POST {self._path} - Status: {response.status}")
        self._reset()
        return response
    
    async def put_request(self, expected_status: int = 200) -> Any:
        """Make PUT request"""
        self._expected_status = expected_status
        logger.info(f"PUT {self._path}", extra={"body": self._body})
        
        response = await self.request.put(
            self._path,
            data=self._body,
            headers=self._headers
        )
        
        logger.info(f"PUT {self._path} - Status: {response.status}")
        self._reset()
        return response
    
    async def delete_request(self, expected_status: int = 204) -> Any:
        """Make DELETE request"""
        self._expected_status = expected_status
        logger.info(f"DELETE {self._path}")
        
        response = await self.request.delete(
            self._path,
            headers=self._headers
        )
        
        logger.info(f"DELETE {self._path} - Status: {response.status}")
        self._reset()
        return response
    
    async def patch_request(self, expected_status: int = 200) -> Any:
        """Make PATCH request"""
        self._expected_status = expected_status
        logger.info(f"PATCH {self._path}", extra={"body": self._body})
        
        response = await self.request.patch(
            self._path,
            data=self._body,
            headers=self._headers
        )
        
        logger.info(f"PATCH {self._path} - Status: {response.status}")
        self._reset()
        return response
    
    def _reset(self):
        """Reset builder state"""
        self._path = ""
        self._params = {}
        self._body = None
        self._headers = {}
        self._expected_status = None
    
    async def set_auth_token(self, token: str):
        """Set authentication token"""
        await self.request.set_extra_http_headers({
            "Authorization": f"Token {token}"
        })
        logger.info("Authentication token set")
    
    async def clear_auth(self):
        """Clear authentication"""
        await self.request.set_extra_http_headers({
            "Authorization": ""
        })
        logger.info("Authentication cleared")


class RequestHandler:
    """Request handler with retry logic"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 30000):
        self.max_retries = max_retries
        self.timeout = timeout
    
    async def execute_request(self, api_client: APIClient, method: str, **kwargs) -> Any:
        """
        Execute request with retry logic
        
        Args:
            api_client: APIClient instance
            method: HTTP method (get, post, put, delete, patch)
            
        Returns:
            Response object
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.max_retries}")
                
                if method.lower() == 'get':
                    response = await api_client.get_request(**kwargs)
                elif method.lower() == 'post':
                    response = await api_client.post_request(**kwargs)
                elif method.lower() == 'put':
                    response = await api_client.put_request(**kwargs)
                elif method.lower() == 'delete':
                    response = await api_client.delete_request(**kwargs)
                elif method.lower() == 'patch':
                    response = await api_client.patch_request(**kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed: {str(e)}")
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    backoff_time = (2 ** attempt) * 1000 / 1000  # Convert to seconds
                    logger.info(f"Retrying in {backoff_time} seconds...")
                    await asyncio.sleep(backoff_time)
        
        raise Exception(f"Request failed after {self.max_retries} attempts: {str(last_error)}")
    
    async def validate_response(self, response, expected_status: int) -> bool:
        """Validate response status"""
        if response.status != expected_status:
            error_message = f"Expected status {expected_status}, but got {response.status}"
            try:
                body = await response.text()
                error_message += f"\nResponse: {body[:500]}"
            except:
                pass
            raise AssertionError(error_message)
        return True
    
    @staticmethod
    async def parse_response(response) -> Dict[str, Any]:
        """Parse response body as JSON"""
        try:
            return await response.json()
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            return {}