"""
"""Configuration module template for web scraper.
Contains all site-specific settings, selectors, and thresholds.

INSTRUCTIONS:
1. Copy this file and rename it to config.py for your target website
2. Update SITE_NAME, BASE_URL, and OUTPUT_CSV for your site
3. Configure SELECTORS based on your target website's HTML structure (use XPath for best accuracy)
4. Adjust DATA_FIELDS to match the data you want to extract
5. Tune performance parameters as needed
"""

# ========== SITE CONFIGURATION ==========
SITE_NAME = "YourSiteName"  # Name of the website you're scraping
BASE_URL = "https://www.example.com/"  # Base URL of the website
REQUIRES_LOGIN = False  # Set to True if login is required

# Login credentials (only if REQUIRES_LOGIN = True)
LOGIN_CREDENTIALS = {"username": "", "password": ""}

# ========== INPUT/OUTPUT FILES ==========
INPUT_CSV = "search_terms.csv"  # CSV with search queries to process
OUTPUT_CSV = "results.csv"  # Output CSV filename
INPUT_COLUMN_NAME = "search_term"  # Column name in input CSV containing search terms

# ========== DATA FIELD DEFINITIONS ==========
# Maps output field names to their extraction config
# Format: "CSV Column Name": {config dict}
DATA_FIELDS = {
    "Search Term": {
        "type": "metadata",  # Not scraped, injected by worker
        "required": True,
        "default": "N/A",
    },
    "Product Title": {
        "type": "scraped",
        "selector": "title",  # References SELECTORS["title"] below
        "required": True,
        "default": "No Title",
        "attribute": None,  # Use .text, or specify attribute name like "href"
    },
    "Price": {
        "type": "scraped",
        "selector": "price",
        "required": True,
        "default": "N/A",
        "attribute": None,
    },
    # Add more fields as needed:
    # "Image URL": {
    #     "type": "scraped",
    #     "selector": "image",
    #     "required": False,
    #     "default": "",
    #     "attribute": "src",  # Extract src attribute from img tag
    # },
}

# Generate OUTPUT_FIELDS list from DATA_FIELDS keys (maintains order)
OUTPUT_FIELDS = list(DATA_FIELDS.keys())

# ========== SELECTORS ==========
# Configure these selectors based on your target website's HTML structure
# Using XPath is recommended for maximum accuracy and flexibility
SELECTORS = {
    # ===== Page Navigation Selectors =====
    "search_bar": {
        "by": "XPATH",
        "value": "//input[@type='search']",
        "fallback": [
            {"by": "XPATH", "value": "//input[@id='search-input']"},
            {"by": "XPATH", "value": "//input[@name='q']"},
        ],
    },
    "results_container": {
        "by": "XPATH",
        "value": "//div[contains(@class, 'results-container')]",
        "fallback": [
            {"by": "XPATH", "value": "//div[@class='results']"},
        ],
    },
    "product_rows": {
        "by": "XPATH",
        "value": "//div[contains(@class, 'product-item')]",
        "fallback": [
            {"by": "XPATH", "value": "//div[@class='product']"},
        ],
    },
    "next_page_button": {
        "by": "XPATH",
        "value": "//a[contains(@class, 'next-page')]",
        "fallback": [
            {"by": "XPATH", "value": "//a[text()='Next']"},
        ],
    },
    # ===== Product Data Selectors =====
    # These must match the selector names used in DATA_FIELDS above
    "title": {
        "by": "XPATH",
        "value": ".//h2[contains(@class, 'product-title')]",
        "fallback": [
            {"by": "XPATH", "value": ".//h2[@class='title']"},
        ],
    },
    "price": {
        "by": "XPATH",
        "value": ".//span[@class='price']",
        "fallback": [
            {"by": "XPATH", "value": ".//span[contains(@class, 'product-price')]"},
        ],
    },
    # Add more selectors as needed to match your DATA_FIELDS
}

# ========== RESOURCE THRESHOLDS ==========
MAX_CPU = 70  # Percentage - pause spawning new bots if CPU exceeds this
MAX_RAM = 80  # Percentage - pause spawning new bots if RAM exceeds this
COOLDOWN_SECONDS = 10  # Cooldown after overload detection
CHECK_INTERVAL = 1  # Seconds between resource checks
WARMUP_SECONDS = 30  # Grace period before enforcing caps

# ========== SPAWN CONTROL ==========
SPAWN_MIN_GAP = 3.0  # Minimum seconds between bot spawns
SPAWN_MAX_GAP = 20.0  # Maximum seconds between bot spawns
SPAWN_JITTER = 0.5  # Random variation in spawn timing
SPINUP_GRACE = 4.0  # Quiet period after each spawn
INITIAL_MAX_BOTS = 9999  # Initial cap (adjusted dynamically)

# ========== WAIT TIMES ==========
PAGE_LOAD_TIMEOUT = 20  # Seconds to wait for page elements
SEARCH_SUBMIT_WAIT = 5  # Seconds to wait after search submission
POST_SCRAPE_DELAY_MIN = 2.0  # Minimum delay after scraping
POST_SCRAPE_DELAY_MAX = 3.5  # Maximum delay after scraping
BETWEEN_PAGES_DELAY = 2.0  # Delay when navigating pagination

# ========== PAGINATION LIMITS ==========
MAX_PAGES_PER_SEARCH = 1  # Maximum pages to scrape per search term (0 = unlimited)
MAX_ITEMS_PER_SEARCH = 15  # Maximum items to scrape per search term (0 = unlimited)
SKIP_EMPTY_PAGES = True  # Stop pagination if a page returns no results

# ========== CHROME OPTIONS ==========
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    # Add more options as needed:
    # "--disable-blink-features=AutomationControlled",
    # "--user-agent=Mozilla/5.0 ...",
]

HEADLESS_MODE = False  # Set to True for headless scraping


# ========== RANDOM DELAYS ==========
def get_random_delay(min_val, max_val):
    """Generate random delay between min and max values."""
    import random

    return random.uniform(min_val, max_val)
