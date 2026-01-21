import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import APIRequestContext
from utils.logger import logger


class RequestHandler:
    """Request handler for API calls"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RequestHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.max_retries = 3
        self.timeout = 30000
        self._initialized = True
    
    async def make_request(
        self,
        request: APIRequestContext,
        method: str,
        url: str,
        **kwargs
    ) -> Any:
        """
        Make HTTP request with retry logic
        
        Args:
            request: APIRequestContext
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Making {method.upper()} request to {url} (Attempt {attempt}/{self.max_retries})")
                
                if method.lower() == 'get':
                    response = await request.get(url, **kwargs)
                elif method.lower() == 'post':
                    response = await request.post(url, **kwargs)
                elif method.lower() == 'put':
                    response = await request.put(url, **kwargs)
                elif method.lower() == 'delete':
                    response = await request.delete(url, **kwargs)
                elif method.lower() == 'patch':
                    response = await request.patch(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                logger.info(f"Request successful: {method.upper()} {url} - Status: {response.status}")
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
    
    async def validate_status(self, response, expected_status: int) -> bool:
        """
        Validate response status
        
        Args:
            response: Response object
            expected_status: Expected HTTP status code
            
        Returns:
            True if status matches
        """
        if response.status != expected_status:
            error_message = f"Expected status {expected_status}, but got {response.status}"
            
            try:
                body = await response.text()
                if body:
                    error_message += f"\nResponse: {body[:500]}"
            except Exception as e:
                logger.warning(f"Failed to read response body: {str(e)}")
            
            logger.error(error_message)
            raise AssertionError(error_message)
        
        return True
    
    @staticmethod
    async def parse_json(response) -> Dict[str, Any]:
        """Parse response as JSON"""
        try:
            return await response.json()
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            return {}
    
    @staticmethod
    async def extract_value(response, json_path: str) -> Any:
        """
        Extract value from JSON response using dot notation
        
        Args:
            response: Response object
            json_path: Path to value (e.g., 'data.user.id')
            
        Returns:
            Extracted value
        """
        data = await RequestHandler.parse_json(response)
        
        keys = json_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise KeyError(f"Path '{json_path}' not found in response")
        
        return value
    
    @staticmethod
    async def wait_for_status(
        request_func,
        expected_status: int,
        max_attempts: int = 10,
        delay: float = 1.0
    ) -> Any:
        """
        Wait for specific status code
        
        Args:
            request_func: Function that makes the request
            expected_status: Expected HTTP status code
            max_attempts: Maximum number of attempts
            delay: Delay between attempts in seconds
            
        Returns:
            Response object
        """
        for attempt in range(max_attempts):
            try:
                response = await request_func()
                if response.status == expected_status:
                    return response
                logger.info(f"Attempt {attempt + 1}: Got status {response.status}, expected {expected_status}")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)
        
        raise TimeoutError(f"Did not receive status {expected_status} after {max_attempts} attempts")