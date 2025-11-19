"""
"""Generic scraper engine - site-agnostic scraping logic.
Uses configuration from config.py for site-specific behavior.

This template provides the core scraping framework with:
- Multi-process parallelization
- Resource management (CPU/RAM monitoring)
- Retry logic for failed searches
- Graceful Chrome driver shutdown
- Pagination support
- CSV input/output handling

NO MODIFICATIONS NEEDED - works with any config.py configuration.
"""

import csv
import time
import random
import traceback
import sys
import os
from datetime import datetime
from multiprocessing import Process, Manager
import psutil
from undetected_chromedriver.patcher import Patcher
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import warnings

# Suppress undetected_chromedriver cleanup warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

# Monkey-patch the Chrome __del__ to suppress handle errors
original_chrome_del = uc.Chrome.__del__


def silent_chrome_del(self):
    """Silently handle Chrome cleanup without printing errors."""
    try:
        original_chrome_del(self)
    except (OSError, Exception):
        pass  # Silently ignore all cleanup errors


uc.Chrome.__del__ = silent_chrome_del

import config


# ---------- Resource Sensing ----------


def is_system_overloaded(max_cpu=None, max_ram=None, sample_interval=0.8):
    """Check if system CPU or RAM usage exceeds thresholds."""
    max_cpu = max_cpu or config.MAX_CPU
    max_ram = max_ram or config.MAX_RAM
    cpu = psutil.cpu_percent(interval=sample_interval)
    ram = psutil.virtual_memory().percent
    return (cpu >= max_cpu) or (ram >= max_ram), cpu, ram


# ---------- Driver Setup ----------


def prepare_chromedriver():
    """Patch and return the path to undetected ChromeDriver."""
    patcher = Patcher()
    patcher.auto()
    return patcher.executable_path


def setup_driver(driver_path, index):
    """Spin up a Chrome driver with configured options."""
    options = uc.ChromeOptions()
    for option in config.CHROME_OPTIONS:
        options.add_argument(option)

    driver = uc.Chrome(
        driver_executable_path=driver_path,
        options=options,
        headless=config.HEADLESS_MODE,
    )

    # Suppress the __del__ error by marking driver as already quit
    # This prevents the garbage collector from trying to quit again
    driver._is_remote_connection = False

    return driver


def graceful_quit(driver, bot_id=None):
    """Gracefully quit the Chrome driver without throwing exceptions."""
    if driver is None:
        return

    # Temporarily suppress stderr to hide Chrome cleanup errors
    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")

    try:
        if bot_id:
            # Restore stderr temporarily to print our message
            sys.stderr = original_stderr
            print(f"[SHUTDOWN] Bot {bot_id} closing browser...")
            sys.stderr = open(os.devnull, "w")

        driver.quit()
    except (OSError, Exception):
        pass  # Silently ignore all cleanup errors
    finally:
        # Restore stderr
        sys.stderr.close()
        sys.stderr = original_stderr

        if bot_id:
            print(f"[SHUTDOWN] Bot {bot_id} shutdown complete.")


# ---------- CSV Handling ----------


def init_output_file(output_file, fields):
    """Initialize output CSV with headers."""
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)


def append_to_csv(output_file, rows, lock):
    """Thread-safe append rows to output CSV."""
    with lock:
        with open(output_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


def load_search_terms(filename):
    """Read list of search terms from CSV into memory."""
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        terms = [
            row[config.INPUT_COLUMN_NAME].strip()
            for row in reader
            if row.get(config.INPUT_COLUMN_NAME)
        ]
    return terms


# ---------- Selector Resolution ----------


def get_element_by_selector(parent, selector_config, wait=None, timeout=10):
    """
    Generic element finder using selector config with fallback support.
    Returns element or None if not found.
    """
    # Try primary selector
    by_type = getattr(By, selector_config["by"])
    value = selector_config["value"]

    try:
        if wait:
            element = wait.until(EC.presence_of_element_located((by_type, value)))
        else:
            element = parent.find_element(by_type, value)
        return element
    except (NoSuchElementException, TimeoutException):
        pass

    # Try fallback selectors if available
    if "fallback" in selector_config:
        for fallback in selector_config["fallback"]:
            try:
                fallback_by = getattr(By, fallback["by"])
                fallback_value = fallback["value"]
                if wait:
                    element = wait.until(
                        EC.presence_of_element_located((fallback_by, fallback_value))
                    )
                else:
                    element = parent.find_element(fallback_by, fallback_value)
                return element
            except (NoSuchElementException, TimeoutException):
                continue

    return None


def get_elements_by_selector(parent, selector_config):
    """
    Generic elements finder (plural) using selector config with fallback support.
    Returns list of elements (empty list if none found).
    """
    # Try primary selector
    by_type = getattr(By, selector_config["by"])
    value = selector_config["value"]

    try:
        elements = parent.find_elements(by_type, value)
        if elements:
            return elements
    except NoSuchElementException:
        pass

    # Try fallback selectors if available
    if "fallback" in selector_config:
        for fallback in selector_config["fallback"]:
            try:
                fallback_by = getattr(By, fallback["by"])
                fallback_value = fallback["value"]
                elements = parent.find_elements(fallback_by, fallback_value)
                if elements:
                    return elements
            except NoSuchElementException:
                continue

    return []


# ---------- Data Extraction ----------


def extract_field_value(product_element, field_config):
    """
    Extract a single field value from a product element.
    Returns the extracted value or the default if extraction fails.
    """
    default_value = field_config.get("default", "N/A")

    if field_config["type"] == "metadata":
        # Metadata fields are injected, not scraped
        return default_value

    # Get selector config
    selector_name = field_config["selector"]
    if selector_name not in config.SELECTORS:
        return default_value

    selector_config = config.SELECTORS[selector_name]

    # Find the element
    element = get_element_by_selector(product_element, selector_config)
    if not element:
        return default_value

    # Extract value
    attribute = field_config.get("attribute")
    if attribute:
        value = element.get_attribute(attribute)
    else:
        value = element.text

    return value.strip() if value else default_value


def extract_product_data(product_element, search_term):
    """
    Extract all configured fields from a product element.
    Returns a list of values matching config.OUTPUT_FIELDS order.
    """
    row = []

    for field_name in config.OUTPUT_FIELDS:
        field_config = config.DATA_FIELDS[field_name]

        # Handle metadata fields
        if field_config["type"] == "metadata":
            if field_name == "Search Term":
                row.append(search_term)
            else:
                row.append(field_config.get("default", "N/A"))
        else:
            # Extract scraped field
            value = extract_field_value(product_element, field_config)
            row.append(value)

    return row


# ---------- Pagination & Scraping ----------


def paginated_results(driver, search_term, csv_lock, bot_id):
    """
    Main scraping loop with pagination support.
    Returns count of items scraped.
    """
    wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT)
    total_scraped = 0
    page_num = 1

    while True:
        # Wait for results container
        try:
            container = get_element_by_selector(
                driver, config.SELECTORS["results_container"], wait=wait
            )
            if not container:
                print(f"[Bot {bot_id}] No results container found on page {page_num}")
                break
        except TimeoutException:
            print(f"[Bot {bot_id}] Timeout waiting for results on page {page_num}")
            break

        # Get product rows
        products = get_elements_by_selector(container, config.SELECTORS["product_rows"])

        if not products:
            print(f"[Bot {bot_id}] No products found on page {page_num}")
            if config.SKIP_EMPTY_PAGES:
                break
            page_num += 1
            continue

        print(f"[Bot {bot_id}] Found {len(products)} products on page {page_num}")

        # Extract data from each product
        batch_rows = []
        for idx, product in enumerate(products):
            # Check item limit
            if (
                config.MAX_ITEMS_PER_SEARCH > 0
                and total_scraped >= config.MAX_ITEMS_PER_SEARCH
            ):
                print(
                    f"[Bot {bot_id}] Reached max items limit ({config.MAX_ITEMS_PER_SEARCH})"
                )
                break

            # Extract product data
            row = extract_product_data(product, search_term)
            batch_rows.append(row)
            total_scraped += 1

            # Optional: Print extracted data for monitoring
            product_title = row[config.OUTPUT_FIELDS.index("Product Title")]
            print(
                f"[Bot {bot_id}] Scraped ({total_scraped}): '{product_title[:60]}...'"
            )

        # Write batch to CSV
        if batch_rows:
            append_to_csv(config.OUTPUT_CSV, batch_rows, csv_lock)

        # Check if we've hit the item limit
        if (
            config.MAX_ITEMS_PER_SEARCH > 0
            and total_scraped >= config.MAX_ITEMS_PER_SEARCH
        ):
            break

        # Check pagination limit
        if config.MAX_PAGES_PER_SEARCH > 0 and page_num >= config.MAX_PAGES_PER_SEARCH:
            print(
                f"[Bot {bot_id}] Reached max pages limit ({config.MAX_PAGES_PER_SEARCH})"
            )
            break

        # Try to find next page button
        next_button = get_element_by_selector(
            driver, config.SELECTORS["next_page_button"]
        )

        if not next_button:
            print(f"[Bot {bot_id}] No next page button found, ending pagination")
            break

        # Click next page
        try:
            next_button.click()
            page_num += 1
            time.sleep(config.BETWEEN_PAGES_DELAY)
        except Exception as e:
            print(f"[Bot {bot_id}] Error clicking next page: {e}")
            break

    print(f"[Bot {bot_id}] Completed: {total_scraped} items scraped")
    return total_scraped


# ---------- Worker Function ----------


def scraper_worker(driver_path, search_term, csv_lock, bot_id, max_retries=1):
    """
    Worker process that scrapes results for a single search term.
    Includes retry logic for failed searches.
    """
    driver = None
    retry_count = 0

    while retry_count <= max_retries:
        try:
            # Setup driver
            driver = setup_driver(driver_path, bot_id)
            print(f"[Bot {bot_id}] Spawned for: '{search_term}'")

            # Navigate to site
            driver.get(config.BASE_URL)
            wait = WebDriverWait(driver, config.PAGE_LOAD_TIMEOUT)

            # Find search bar
            search_bar = get_element_by_selector(
                driver, config.SELECTORS["search_bar"], wait=wait
            )

            if not search_bar:
                print(f"[Bot {bot_id}] Could not find search bar")
                raise Exception("Search bar not found")

            # Enter search term
            search_bar.clear()
            search_bar.send_keys(search_term)
            search_bar.send_keys(Keys.RETURN)

            # Wait for results to load
            time.sleep(config.SEARCH_SUBMIT_WAIT)

            # Scrape paginated results
            items_scraped = paginated_results(driver, search_term, csv_lock, bot_id)

            print(f"[Bot {bot_id}] Completed: {items_scraped} items scraped")

            # Success - exit retry loop
            break

        except Exception as e:
            retry_count += 1
            print(
                f"[Bot {bot_id}] Error (attempt {retry_count}/{max_retries + 1}): {e}"
            )

            if retry_count <= max_retries:
                print(f"[Bot {bot_id}] Retrying...")
                if driver:
                    graceful_quit(driver)
                    driver = None
                time.sleep(3)  # Wait before retry
            else:
                print(
                    f"[Bot {bot_id}] Max retries reached, giving up on '{search_term}'"
                )
                traceback.print_exc()

        finally:
            # Add random delay before cleanup
            time.sleep(
                config.get_random_delay(
                    config.POST_SCRAPE_DELAY_MIN, config.POST_SCRAPE_DELAY_MAX
                )
            )

    # Cleanup
    if driver:
        graceful_quit(driver, bot_id)


# ---------- Main Orchestrator ----------


def main():
    """Main orchestrator - spawns worker processes for each search term."""
    print(f"========== {config.SITE_NAME} Scraper ==========")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Prepare ChromeDriver
    print("Preparing ChromeDriver...")
    driver_path = prepare_chromedriver()
    print(f"ChromeDriver ready: {driver_path}\n")

    # Load search terms
    print(f"Loading search terms from {config.INPUT_CSV}...")
    search_terms = load_search_terms(config.INPUT_CSV)
    print(f"Loaded {len(search_terms)} search terms\n")

    # Initialize output CSV
    init_output_file(config.OUTPUT_CSV, config.OUTPUT_FIELDS)
    print(f"Initialized output file: {config.OUTPUT_CSV}\n")

    # Create shared lock for CSV writing
    manager = Manager()
    csv_lock = manager.Lock()

    # Track active processes
    processes = []
    max_concurrent_bots = config.INITIAL_MAX_BOTS
    start_time = time.time()

    # Spawn workers
    for idx, term in enumerate(search_terms):
        bot_id = idx + 1

        # Wait for available slot
        while len([p for p in processes if p.is_alive()]) >= max_concurrent_bots:
            time.sleep(config.CHECK_INTERVAL)

            # Check system resources (after warmup)
            if time.time() - start_time > config.WARMUP_SECONDS:
                overloaded, cpu, ram = is_system_overloaded()
                if overloaded:
                    print(
                        f"[RESOURCE] System overloaded (CPU: {cpu:.1f}%, RAM: {ram:.1f}%) - cooling down..."
                    )
                    time.sleep(config.COOLDOWN_SECONDS)

        # Spawn worker process
        p = Process(target=scraper_worker, args=(driver_path, term, csv_lock, bot_id))
        p.start()
        processes.append(p)

        # Stagger spawns
        spawn_delay = config.get_random_delay(
            config.SPAWN_MIN_GAP, config.SPAWN_MAX_GAP
        )
        time.sleep(spawn_delay)

    # Wait for all workers to complete
    print("\n[MAIN] Waiting for all bots to complete...")
    for p in processes:
        p.join()

    print(f"\n========== Scraping Complete ==========")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results saved to: {config.OUTPUT_CSV}")


if __name__ == "__main__":
    main()
