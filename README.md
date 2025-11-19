# Scraper Seed 🌱

A production-ready, highly configurable web scraping template that separates site-specific configuration from core scraping logic. Built with **Selenium** and **undetected-chromedriver** for robust, parallel web scraping with intelligent filtering and resource management.

## 🎯 Overview

This template provides a complete scraping framework that you can customize for any website by simply updating configuration files—no need to modify the core scraping engine. Perfect for e-commerce scraping, product research, price monitoring, and data collection.

### Key Features

- **🔧 Zero-Code Customization**: Configure selectors and behavior via `config.py`—no engine modifications needed
- **⚡ Multi-Process Parallelization**: Concurrent workers with automatic resource monitoring (CPU/RAM)
- **🔄 Pagination Support**: Automatic multi-page scraping with configurable limits
- **🛡️ Anti-Detection**: Uses undetected-chromedriver with randomized delays and human-like behavior
- **💪 Retry Logic**: Automatic retries for failed searches with graceful error handling
- **📊 CSV Input/Output**: Bulk search term processing with structured data export
- **🎛️ Resource Management**: Automatic throttling based on system CPU/RAM thresholds

---

## 📁 Project Structure

```
Scraper_Seed/
├── config_template.py          # Site-specific configuration template
├── scraper_engine_template.py  # Core scraping engine (no modifications needed)
├── search_terms.csv            # Input: list of search queries
└── results.csv                 # Output: scraped data (generated)
```

### File Roles

| File | Purpose | Modify? |
|------|---------|---------|
| `config_template.py` | All site-specific settings, selectors, and filters | ✅ Yes |
| `scraper_engine_template.py` | Generic scraping logic and worker orchestration | ❌ No |
| `search_terms.csv` | Input search terms to process | ✅ Yes |
| `results.csv` | Generated output with scraped data | Auto-generated |

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install selenium undetected-chromedriver psutil
```

### 1. Setup Configuration

1. **Copy the config template:**
   ```bash
   cp config_template.py config.py
   ```

2. **Update basic settings in `config.py`:**
   ```python
   SITE_NAME = "Amazon"
   BASE_URL = "https://www.amazon.com/"
   OUTPUT_CSV = "amazon_results.csv"
   ```

3. **Configure XPath selectors** (see detailed guide below)

### 2. Create Input File

Create `search_terms.csv` with your search queries:

```csv
search_term
wireless keyboard
gaming mouse
laptop stand
```

### 3. Run the Scraper

```bash
python scraper_engine_template.py
```

That's it! Results will be saved to your configured output CSV.

---

## ⚙️ Configuration Guide

### 🎯 Step-by-Step: Adapting for a New Website

#### Step 1: Update Site Information

```python
# In config.py
SITE_NAME = "YourTargetSite"
BASE_URL = "https://www.targetsite.com/"
OUTPUT_CSV = "scraped_data.csv"
```

#### Step 2: Configure XPath Selectors

**The most important step!** You need to identify XPath selectors for your target website.

**Why XPath?** XPath provides superior accuracy and precision compared to CSS selectors:
- Navigate complex DOM structures with ease
- Access parent/sibling elements (impossible with CSS)
- Use powerful predicates for exact matching
- More resilient to HTML structure changes
- Support for text content matching

**How to find XPath selectors:**
1. Visit your target website
2. Right-click an element → "Inspect"
3. In DevTools, right-click the HTML element → Copy → Copy XPath
4. Refine the XPath for better accuracy (see tips below)

**Example selector configuration:**

```python
SELECTORS = {
    "search_bar": {
        "by": "XPATH",
        "value": "//input[@id='search-input']",
        "fallback": [
            {"by": "XPATH", "value": "//input[@name='q']"},
            {"by": "XPATH", "value": "//input[@type='search']"}
        ]
    },
    "product_rows": {
        "by": "XPATH", 
        "value": "//div[contains(@class, 'product-card')]",
        "fallback": [
            {"by": "XPATH", "value": "//div[@class='item']"}
        ]
    },
    "title": {
        "by": "XPATH",
        "value": ".//h2[contains(@class, 'product-title')]",
        "fallback": [
            {"by": "XPATH", "value": ".//h2[@class='title']"}
        ]
    },
    "price": {
        "by": "XPATH",
        "value": ".//span[@class='price-value']"
    }
}
```

**XPath Pro Tips:**
- Use **relative XPath** (`.//`) within product elements for nested searches
- Use `[@attribute='value']` for exact matches
- Use `[contains(@attribute, 'value')]` for partial matches
- Combine conditions: `//div[@class='product' and @data-available='true']`
- Match by text: `//button[text()='Add to Cart']`
- Navigate hierarchy: `//div[@class='parent']//span[@class='child']`

**Selector Types** (use `By` constant):
- `XPATH` - XPath expression **(recommended for accuracy)**
- `CSS_SELECTOR` - CSS selector syntax
- `ID` - Element ID
- `CLASS_NAME` - Class name
- `NAME` - Name attribute
- `LINK_TEXT` - Exact link text
- `PARTIAL_LINK_TEXT` - Partial link text
- `TAG_NAME` - HTML tag name

#### Step 3: Define Data Fields

Map what data you want to extract (field names reference your XPath selectors):

```python
DATA_FIELDS = {
    "Search Term": {
        "type": "metadata",  # Auto-injected, not scraped
        "required": True,
        "default": "N/A"
    },
    "Product Title": {
        "type": "scraped",
        "selector": "title",  # References SELECTORS["title"] XPath
        "required": True,
        "default": "No Title",
        "attribute": None  # Use .text, or specify attribute like "href"
    },
    "Price": {
        "type": "scraped",
        "selector": "price",  # References SELECTORS["price"] XPath
        "required": True,
        "default": "N/A",
        "attribute": None
    },
    "Image URL": {
        "type": "scraped",
        "selector": "image",  # References SELECTORS["image"] XPath
        "required": False,
        "default": "",
        "attribute": "src"  # Extract src attribute from <img>
    },
    "Product Link": {
        "type": "scraped",
        "selector": "link",  # References SELECTORS["link"] XPath
        "required": False,
        "default": "",
        "attribute": "href"  # Extract href from <a>
    }
}
```

**Field Configuration:**
- `type`: `"metadata"` (injected) or `"scraped"` (extracted from HTML)
- `selector`: Name of selector from `SELECTORS` dict
- `required`: Whether field is mandatory
- `default`: Default value if extraction fails
- `attribute`: HTML attribute to extract (or `None` for text content)

#### Step 4: Tune Performance Settings

**Resource Limits:**
```python
MAX_CPU = 70  # Pause spawning at 70% CPU
MAX_RAM = 80  # Pause spawning at 80% RAM
INITIAL_MAX_BOTS = 5  # Concurrent browser instances
```

**Timing:**
```python
PAGE_LOAD_TIMEOUT = 20  # Seconds
SPAWN_MIN_GAP = 3.0  # Min seconds between bot spawns
SPAWN_MAX_GAP = 8.0  # Max seconds between bot spawns
POST_SCRAPE_DELAY_MIN = 2.0  # Min delay after scraping
POST_SCRAPE_DELAY_MAX = 4.0  # Max delay after scraping
```

**Pagination:**
```python
MAX_PAGES_PER_SEARCH = 3  # Max pages per search (0 = unlimited)
MAX_ITEMS_PER_SEARCH = 20  # Max items per search (0 = unlimited)
```

**Headless Mode:**
```python
HEADLESS_MODE = False  # Set True to hide browser windows
```

---

## 📖 Advanced Usage

### Custom Data Extraction with XPath

Extract any HTML attribute or nested content using precise XPath:

```python
# Extract href attribute
"Product URL": {
    "type": "scraped",
    "selector": "product_link",  # XPath: ".//a[@class='product-link']"
    "attribute": "href"
}

# Extract data attributes using XPath
"Product ID": {
    "type": "scraped",
    "selector": "product_card",  # XPath: ".//div[@data-product-id]"
    "attribute": "data-product-id"
}

# Extract image source with specific XPath
"Thumbnail": {
    "type": "scraped",
    "selector": "thumbnail_img",  # XPath: ".//img[@class='thumbnail']"
    "attribute": "src"
}

# XPath-specific: Extract nested text
"Brand": {
    "type": "scraped",
    "selector": "brand",  # XPath: ".//div[@class='brand-info']/span"
    "attribute": None
}

# XPath-specific: Match by text content
"In Stock": {
    "type": "scraped",
    "selector": "stock",  # XPath: ".//span[contains(text(), 'In Stock')]"
    "attribute": None
}
```

### Login Support

For sites requiring authentication:

```python
REQUIRES_LOGIN = True
LOGIN_CREDENTIALS = {
    "username": "your_username",
    "password": "your_password"
}
```

**Note:** You'll need to implement the login logic in the engine or add login selectors.

### Debugging Tips

1. **Start with headless mode off:**
   ```python
   HEADLESS_MODE = False  # Watch what the bot is doing
   ```

2. **Test with one bot:**
   ```python
   INITIAL_MAX_BOTS = 1  # Single worker for debugging
   ```

3. **Increase timeouts if pages load slowly:**
   ```python
   PAGE_LOAD_TIMEOUT = 30
   SEARCH_SUBMIT_WAIT = 8
   ```

---

## 🏗️ Architecture

### How It Works

```
┌─────────────────────┐
│   search_terms.csv  │
│   [Input Queries]   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    config.py        │
│  [Site Settings]    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  scraper_engine_template.py         │
│  ┌───────────────────────────────┐  │
│  │ 1. Load search terms          │  │
│  │ 2. Spawn parallel workers     │  │
│  │ 3. Monitor system resources   │  │
│  │ 4. Each worker:               │  │
│  │    - Opens Chrome browser     │  │
│  │    - Searches for term        │  │
│  │    - Extracts data            │  │
│  │    - Navigates pagination     │  │
│  │    - Writes to CSV            │  │
│  │ 5. Graceful shutdown          │  │
│  └───────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────┐
        │  results.csv │
        │   [Output]   │
        └──────────────┘
```

### Worker Process Flow

```
Worker Spawned → Navigate to Site → Find Search Bar → Enter Query
       ↓
   Submit Search → Wait for Results → Extract Product Data
       ↓
   Write to CSV → Next Page? → Yes: Repeat | No: Complete → Shutdown
```

---

## 🛠️ Customization Examples

### Example 1: E-Commerce Product Scraper

```python
# config.py
SITE_NAME = "E-Shop"
BASE_URL = "https://www.eshop.com/"

DATA_FIELDS = {
    "Search Term": {"type": "metadata", "required": True, "default": "N/A"},
    "Product Name": {"type": "scraped", "selector": "title", "required": True, "default": "No Title", "attribute": None},
    "Price": {"type": "scraped", "selector": "price", "required": True, "default": "N/A", "attribute": None},
    "Rating": {"type": "scraped", "selector": "rating", "required": False, "default": "0", "attribute": None},
    "Review Count": {"type": "scraped", "selector": "review_count", "required": False, "default": "0", "attribute": None},
    "Availability": {"type": "scraped", "selector": "stock_status", "required": False, "default": "Unknown", "attribute": None}
}

# Using XPath for precise element targeting
SELECTORS = {
    "search_bar": {"by": "XPATH", "value": "//input[@id='search']"},
    "product_rows": {"by": "XPATH", "value": "//div[contains(@class, 'product-item')]"},
    "title": {"by": "XPATH", "value": ".//h3[@class='product-name']"},
    "price": {"by": "XPATH", "value": ".//span[contains(@class, 'current-price')]"},
    "rating": {"by": "XPATH", "value": ".//div[@class='rating-stars']/@title"},
    "review_count": {"by": "XPATH", "value": ".//span[@class='review-count']"},
    "stock_status": {"by": "XPATH", "value": ".//span[@class='availability']"},
    "next_page_button": {"by": "XPATH", "value": "//a[contains(@class, 'next-page')] | //button[text()='Next']"}
}

MAX_PAGES_PER_SEARCH = 5
MAX_ITEMS_PER_SEARCH = 50
```

### Example 2: Price Monitoring

```python
# config.py - Minimal fields for price tracking
DATA_FIELDS = {
    "Timestamp": {"type": "metadata", "required": True, "default": ""},
    "Product": {"type": "scraped", "selector": "title", "required": True, "default": "Unknown", "attribute": None},
    "Current Price": {"type": "scraped", "selector": "price", "required": True, "default": "N/A", "attribute": None},
    "Original Price": {"type": "scraped", "selector": "original_price", "required": False, "default": "N/A", "attribute": None}
}

# Run periodically via cron/scheduler
```

---

## 🐛 Troubleshooting

### Common Issues

**"Could not find search bar"**
- Verify your XPath `search_bar` selector is correct
- Test XPath in browser console: `$x("//input[@id='search']")`
- Try adding fallback XPath selectors
- Increase `PAGE_LOAD_TIMEOUT`
- Use `contains()` for dynamic class names

**"No products found on page"**
- Check `product_rows` XPath selector
- Test in console: `$x("//div[contains(@class, 'product')]")`
- Inspect HTML to verify element exists
- Ensure XPath starts with `//` for absolute or `.//` for relative paths
- Try disabling JavaScript blocking

**"XPath returns wrong elements"**
- Use more specific predicates: `[@class='exact-match']` vs `[contains(@class, 'partial')]`
- Add position filters: `(//div[@class='product'])[1]` for first element
- Combine conditions: `//div[@class='product' and not(@class='sponsored')]`

**"System overloaded" messages**
- Reduce `INITIAL_MAX_BOTS`
- Increase `MAX_CPU` and `MAX_RAM` thresholds
- Add longer delays between spawns

**Chrome crashes or hangs**
- Enable `HEADLESS_MODE = False` to debug
- Reduce concurrent bots
- Increase system resources
- Check ChromeDriver version compatibility

**No data extracted**
- Verify data field selectors are correct
- Test XPath selectors in browser console
- Check if `attribute` is set correctly for the field type
- Ensure elements exist on the page after search

---

## 📊 Output Format

Results are saved to CSV with configured fields:

```csv
Search Term,Product Title,Price,Image URL,Product Link
wireless keyboard,Logitech K380 Wireless Keyboard,$29.99,https://...,https://...
wireless keyboard,Microsoft Wireless Keyboard 850,$19.99,https://...,https://...
gaming mouse,Razer DeathAdder V2 Gaming Mouse,$69.99,https://...,https://...
```

---

## 🔒 Best Practices

### Ethical Scraping

1. **Respect robots.txt**: Check the site's robots.txt before scraping
2. **Rate limiting**: Use appropriate delays to avoid overloading servers
3. **Terms of Service**: Review and comply with website ToS
4. **Attribution**: Credit data sources when publishing results
5. **Personal data**: Avoid scraping personal/private information

### Performance Optimization

1. **Start small**: Test with 1-2 bots before scaling
2. **Monitor resources**: Keep CPU/RAM under 80%
3. **Use headless mode**: Faster and less resource-intensive
4. **Optimize XPath**: Use specific predicates and avoid `//` when `.//` suffices
5. **Limit pagination**: Set reasonable `MAX_PAGES_PER_SEARCH`
6. **XPath efficiency**: Prefer `[@id='value']` over `//*[@id='value']`

### Maintenance

1. **Selector updates**: Websites change—monitor for broken selectors
2. **Error logs**: Review logs for patterns of failures
3. **Version control**: Track config changes in git
4. **Testing**: Validate with small batches before full runs

---

## 📝 License

This is a template project. Use it for your own projects, modify as needed, and build something awesome! 🚀

---

## 🤝 Contributing

Found a bug or have an improvement? Feel free to fork and submit pull requests!

---

## 💡 Tips & Tricks

- **Quick testing**: Use a single search term to test XPath selector changes
- **Browser console XPath testing**: Use `$x("your-xpath-here")` in Chrome DevTools console
- **Fallback selectors**: Always provide fallback XPath options for robustness
- **Resource monitoring**: Watch the console for CPU/RAM metrics
- **Incremental development**: Add one field at a time and test
- **Save configs**: Keep site-specific configs as separate files (e.g., `config_amazon.py`)
- **XPath cheat sheet**: 
  - `//*` = any element
  - `//div` = all divs
  - `.//span` = spans within current context
  - `[@attr='val']` = exact attribute match
  - `[contains(@attr, 'val')]` = partial match
  - `[text()='exact']` = exact text match
  - `[1]` = first element (XPath is 1-indexed)
  - `parent::div` = parent element
  - `following-sibling::span` = next sibling

---

**Happy Scraping! 🎉**
