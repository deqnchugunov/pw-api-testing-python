from typing import Dict, Any, Optional
import asyncio
from utils.logger import logger


class APIHelper:
    """Helper class for API operations"""
    
    def __init__(self, api_client):
        self.api = api_client
    
    async def create_article_and_get_slug(self, article_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create article and return slug
        
        Args:
            article_data: Article data (optional)
            
        Returns:
            Article slug
        """
        from utils.data_generator import get_new_random_article
        
        if article_data is None:
            article_data = get_new_random_article()
        
        response = await self.api \
            .path("/articles") \
            .body(article_data) \
            .post_request(201)
        
        response_body = await response.json()
        return response_body["article"]["slug"]
    
    async def delete_article_by_slug(self, slug: str) -> bool:
        """
        Delete article by slug
        
        Args:
            slug: Article slug
            
        Returns:
            True if successful
        """
        try:
            await self.api \
                .path(f"/articles/{slug}") \
                .delete_request(204)
            return True
        except Exception as e:
            logger.error(f"Failed to delete article {slug}: {str(e)}")
            return False
    
    async def get_article_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get article by slug
        
        Args:
            slug: Article slug
            
        Returns:
            Article data or None
        """
        try:
            response = await self.api \
                .path(f"/articles/{slug}") \
                .get_request(200)
            
            return await response.json()
        except Exception as e:
            logger.error(f"Failed to get article {slug}: {str(e)}")
            return None
    
    async def wait_for_article_creation(self, slug: str, max_attempts: int = 10, delay: float = 1.0) -> bool:
        """
        Wait for article to be created
        
        Args:
            slug: Article slug
            max_attempts: Maximum attempts
            delay: Delay between attempts
            
        Returns:
            True if article exists
        """
        for attempt in range(max_attempts):
            article = await self.get_article_by_slug(slug)
            if article is not None:
                logger.info(f"Article {slug} created after {attempt + 1} attempts")
                return True
            
            logger.info(f"Waiting for article {slug} (attempt {attempt + 1}/{max_attempts})")
            await asyncio.sleep(delay)
        
        logger.error(f"Article {slug} not created after {max_attempts} attempts")
        return False
    
    async def extract_slug_from_title(self, title: str) -> str:
        """
        Extract slug ID from title
        
        Args:
            title: Article title
            
        Returns:
            Slug ID
        """
        import re
        match = re.search(r'\[(.*?)\]', title)
        return match.group(1) if match else ''
    
    async def validate_article_structure(self, article: Dict[str, Any]) -> bool:
        """
        Validate article structure
        
        Args:
            article: Article data
            
        Returns:
            True if valid
        """
        required_fields = ["slug", "title", "description", "body", "createdAt", "updatedAt", "author"]
        
        if "article" not in article:
            return False
        
        article_data = article["article"]
        
        for field in required_fields:
            if field not in article_data:
                return False
        
        # Validate slug pattern
        slug = article_data["slug"]
        pattern = r'^.*?(\d{1,3}\.[A-Z]{2}\.\d{4})$|^(\d{4}\.\d{2}\.\d{4})$'
        if not re.match(pattern, slug):
            return False
        
        return True
    
    async def batch_create_articles(self, count: int) -> list:
        """
        Create multiple articles
        
        Args:
            count: Number of articles to create
            
        Returns:
            List of created article slugs
        """
        from utils.data_generator import get_new_random_article
        
        slugs = []
        
        for i in range(count):
            article_data = get_new_random_article()
            
            try:
                response = await self.api \
                    .path("/articles") \
                    .body(article_data) \
                    .post_request(201)
                
                response_body = await response.json()
                slugs.append(response_body["article"]["slug"])
                
                logger.info(f"Created article {i + 1}/{count}: {response_body['article']['title']}")
                
            except Exception as e:
                logger.error(f"Failed to create article {i + 1}: {str(e)}")
        
        return slugs