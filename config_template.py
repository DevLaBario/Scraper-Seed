"""
Configuration module template for web scraper.
Contains all site-specific settings, selectors, and thresholds.

INSTRUCTIONS:
1. Copy this file and rename it to config.py for your target website
2. Update SITE_NAME, BASE_URL, and OUTPUT_CSV for your site
3. Configure SELECTORS based on your target website's HTML structure
4. Adjust DATA_FIELDS to match the data you want to extract
5. Tune filtering parameters (IGNORE_WORDS, EXCLUSION_KEYWORDS, etc.) as needed
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
SELECTORS = {
    # ===== Page Navigation Selectors =====
    "search_bar": {
        "by": "CSS_SELECTOR",
        "value": "input[type='search']",
        "fallback": [
            {"by": "ID", "value": "search-input"},
            {"by": "NAME", "value": "q"},
        ],
    },
    "results_container": {
        "by": "CSS_SELECTOR",
        "value": "div.results-container",
        "fallback": [
            {"by": "CLASS_NAME", "value": "results"},
        ],
    },
    "product_rows": {
        "by": "CSS_SELECTOR",
        "value": "div.product-item",
        "fallback": [
            {"by": "CLASS_NAME", "value": "product"},
        ],
    },
    "next_page_button": {
        "by": "CSS_SELECTOR",
        "value": "a.next-page",
        "fallback": [
            {"by": "LINK_TEXT", "value": "Next"},
        ],
    },
    # ===== Product Data Selectors =====
    # These must match the selector names used in DATA_FIELDS above
    "title": {
        "by": "CSS_SELECTOR",
        "value": "h2.product-title",
        "fallback": [
            {"by": "CLASS_NAME", "value": "title"},
        ],
    },
    "price": {
        "by": "CSS_SELECTOR",
        "value": "span.price",
        "fallback": [
            {"by": "CLASS_NAME", "value": "product-price"},
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

# ========== RESULT FILTERING ==========
# Skip first N results (useful for skipping sponsored/featured listings)
SKIP_FIRST_N_RESULTS = 0

# Minimum keyword match threshold (0.0 to 1.0)
# How many important words from search term must appear in product title
MIN_KEYWORD_MATCH_RATIO = 0.5  # 50% of keywords must match

# Words to ignore when matching (common filler words and brand names)
IGNORE_WORDS = {
    "for",
    "the",
    "and",
    "or",
    "with",
    "a",
    "an",
    "in",
    "on",
    "at",
    "to",
    "of",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    # Add brand names or other words to ignore for your use case
}

# Exclusion keywords - skip products containing these terms
EXCLUSION_KEYWORDS = [
    # Add terms you want to exclude (e.g., "refurbished", "compatible", etc.)
]

# Part type keywords - helps distinguish between different product types
# Example: prevents mixing "transfer roller" with "pickup roller"
PART_TYPE_KEYWORDS = [
    # Add part type phrases specific to your products
    # Example: "transfer roller", "separation pad", "toner cartridge"
]

# Enable/disable filtering
ENABLE_KEYWORD_MATCHING = True  # Filter by keyword match ratio
ENABLE_EXCLUSION_FILTER = True  # Filter by exclusion keywords
ENABLE_MODEL_VALIDATION = True  # Validate model numbers appear in title
ENABLE_PART_TYPE_VALIDATION = True  # Validate part type matches

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
