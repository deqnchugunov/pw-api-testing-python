import pytest
import re
from utils.data_generator import get_new_random_article


@pytest.mark.api
class TestExample:
    """Example API tests matching screenshot patterns"""
    
    @pytest.mark.asyncio
    async def test_get_articles(self, api, expect):
        """Get Articles - matching screenshot pattern"""
        response = await api \
            .path("/articles") \
            .params({"limit": 10, "offset": 0}) \
            .get_request(200)
        
        await expect.to_match_schema(response, "articles", "get_articles")
        
        response_body = await response.json()
        expect.to_be_greater_than_or_equal(len(response_body["articles"]), 10)
        expect.to_be_greater_than_or_equal(response_body["articlesCount"], 10)
        
        # Verify each article's slug matches its title format
        for article in response_body["articles"]:
            expected_pattern = r'^.*?(\d{1,3}\.[A-Z]{2}\.\d{4})$|^(\d{4}\.\d{2}\.\d{4})$'
            expect.to_match_pattern(article["slug"], expected_pattern)
    
    @pytest.mark.asyncio
    async def test_get_test_tags(self, api, expect):
        """Get Test Tags - matching screenshot pattern"""
        response = await api \
            .path("/tags") \
            .get_request(200)
        
        await expect.to_match_schema(response, "tags", "get_tags")
        
        response_body = await response.json()
        expect.to_be_truthy(response_body["tags"][0])
        expect.to_be_greater_than_or_equal(len(response_body["tags"]), 10)
    
    @pytest.mark.asyncio
    async def test_create_and_delete_article(self, api, expect):
        """Create and Delete Article - matching screenshot pattern"""
        article_request = get_new_random_article()
        slug_id = article_request["article"]["title"].split("[")[1].split("]")[0]
        
        # Create article
        create_article_response = await api \
            .path("/articles") \
            .body(article_request) \
            .post_request(201)
        
        await expect.to_match_snapshot(create_article_response, "articles", "post_articles")
        
        created_article = await create_article_response.json()
        expect.to_contain(created_article["article"]["title"], slug_id)
        
        # Get articles and verify
        articles_response = await api \
            .path("/articles") \
            .params({"limit": 10, "offset": 0}) \
            .get_request(200)
        
        await expect.to_match_snapshot(articles_response, "articles", "get_articles")
        
        articles_body = await articles_response.json()
        expect.to_contain(articles_body["articles"][0]["title"], slug_id)
        
        # Delete article
        await api \
            .path(f"/articles/{slug_id}") \
            .delete_request(204)
        
        # Verify article was deleted
        articles_response_two = await api \
            .path("/articles") \
            .params({"limit": 10, "offset": 0}) \
            .get_request(200)
        
        await expect.to_match_snapshot(articles_response_two, "articles", "get_articles")
        
        articles_body_two = await articles_response_two.json()
        expect.to_be_truthy(articles_body_two["articles"][0]["title"])
    
    @pytest.mark.asyncio
    async def test_article_schema_validation(self, api, expect):
        """Test article schema validation"""
        response = await api \
            .path("/articles") \
            .params({"limit": 1}) \
            .get_request(200)
        
        await expect.to_have_status_code(response, 200)
        
        response_body = await response.json()
        
        # Additional validation can be added here
        assert "articles" in response_body
        assert isinstance(response_body["articles"], list)
    
    @pytest.mark.asyncio
    async def test_response_time(self, api, expect):
        """Test response time"""
        import time
        
        start_time = time.time()
        response = await api \
            .path("/articles") \
            .get_request(200)
        end_time = time.time()
        
        response_time = end_time - start_time
        logger.info(f"Response time: {response_time:.2f} seconds")
        
        # Assert response time is less than 2 seconds
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s limit"