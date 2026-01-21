import pytest


@pytest.mark.smoke
class TestSmoke:
    """Smoke tests for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_api_health_check(self, api, expect):
        """API Health Check"""
        response = await api \
            .path("/health") \
            .get_request(200)
        
        await expect.to_have_status_code(response, 200)
        
        response_body = await response.json()
        expect.to_equal(response_body.get("status"), "OK")
    
    @pytest.mark.asyncio
    async def test_articles_endpoint_availability(self, api):
        """Articles Endpoint Availability"""
        response = await api \
            .path("/articles") \
            .params({"limit": 1}) \
            .get_request(200)
        
        assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_tags_endpoint_availability(self, api):
        """Tags Endpoint Availability"""
        response = await api \
            .path("/tags") \
            .get_request(200)
        
        assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_create_article_smoke_test(self, api, expect):
        """Create Article Smoke Test"""
        article_data = {
            "article": {
                "title": "Smoke Test Article",
                "description": "This is a smoke test",
                "body": "Smoke test content",
                "tagList": ["test", "smoke"]
            }
        }
        
        response = await api \
            .path("/articles") \
            .body(article_data) \
            .post_request(201)
        
        await expect.to_have_status_code(response, 201)
        
        response_body = await response.json()
        expect.to_equal(response_body["article"]["title"], "Smoke Test Article")
    
    @pytest.mark.asyncio
    async def test_authentication(self, api, data_generator):
        """Test authentication"""
        user_data = data_generator.get_new_random_user()
        
        # Register user
        response = await api \
            .path("/users") \
            .body(user_data) \
            .post_request(201)
        
        assert response.status == 201
        
        response_body = await response.json()
        token = response_body["user"]["token"]
        
        # Set auth token
        await api.set_auth_token(token)
        
        # Test authenticated endpoint
        response = await api \
            .path("/user") \
            .get_request(200)
        
        assert response.status == 200
        
        # Clear auth
        await api.clear_auth()