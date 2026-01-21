import pytest
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Playwright

# Load environment variables
load_dotenv()

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        help="Environment to run tests against: dev, staging, prod"
    )
    parser.addoption(
        "--browser",
        action="store",
        default="chromium",
        help="Browser to run tests in: chromium, firefox, webkit"
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=True,
        help="Run tests in headless mode"
    )

@pytest.fixture(scope="session")
def env(request):
    """Get environment from command line"""
    return request.config.getoption("--env")

@pytest.fixture(scope="session")
def base_url(env):
    """Get base URL based on environment"""
    urls = {
        "dev": os.getenv("DEV_BASE_URL", "https://api.realworld.io/api"),
        "staging": os.getenv("STAGING_BASE_URL", "https://api.realworld.io/api"),
        "prod": os.getenv("PROD_BASE_URL", "https://api.realworld.io/api")
    }
    return urls.get(env, urls["dev"])

@pytest.fixture(scope="session")
async def playwright():
    """Playwright instance"""
    async with async_playwright() as p:
        yield p

@pytest.fixture(scope="session")
async def browser(playwright, request):
    """Browser instance"""
    browser_name = request.config.getoption("--browser")
    headless = request.config.getoption("--headless")
    
    if browser_name == "chromium":
        browser = await playwright.chromium.launch(headless=headless)
    elif browser_name == "firefox":
        browser = await playwright.firefox.launch(headless=headless)
    elif browser_name == "webkit":
        browser = await playwright.webkit.launch(headless=headless)
    else:
        raise ValueError(f"Unsupported browser: {browser_name}")
    
    yield browser
    await browser.close()

@pytest.fixture
async def api_request_context(browser, base_url):
    """API request context"""
    context = await browser.new_context(base_url=base_url)
    request_context = context.request
    
    # Set default headers
    await request_context.set_extra_http_headers({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "PW-API-Testing-Python/1.0"
    })
    
    yield request_context
    await context.close()

@pytest.fixture
def api(api_request_context):
    """API client fixture"""
    from utils.fixtures import APIClient
    return APIClient(api_request_context)

@pytest.fixture
def data_generator():
    """Data generator fixture"""
    from utils.data_generator import DataGenerator
    return DataGenerator()

@pytest.fixture
def request_handler():
    """Request handler fixture"""
    from utils.request_handler import RequestHandler
    return RequestHandler()

@pytest.fixture
def expect():
    """Custom expect fixture"""
    from utils.custom_expect import expect
    return expect

# Hook for test setup
def pytest_configure(config):
    """Configure pytest"""
    # Create test results directory
    os.makedirs("test-results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Set environment variables
    config.option.base_url = os.getenv("BASE_URL", "https://api.realworld.io/api")

# Hook for test teardown
def pytest_unconfigure(config):
    """Cleanup after tests"""
    pass