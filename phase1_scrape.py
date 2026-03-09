# phase1_scrape.py
# Save in: lost_found_reunion/phase1_scrape.py
#
# WHAT THIS FILE DOES:
# 1. Scrapes product data from Fake Store API (free, no auth needed)
#    In a real project you'd use BeautifulSoup on Amazon/Flipkart
# 2. Downloads product images into images/ folder
# 3. Uses Ollama (llama3.2) to generate "lost item" descriptions
# 4. Saves everything to data/scraped_products.csv
#
# TOOLS USED: requests, BeautifulSoup, pandas, Pillow, ollama

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import json
import ollama
from PIL import Image
from io import BytesIO
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# All paths are relative to the project root folder
# ─────────────────────────────────────────────────────────────
IMAGES_DIR   = "images"           # folder where images are saved
DATA_DIR     = "data"             # folder where CSV files are saved
OUTPUT_CSV   = "data/scraped_products.csv"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(DATA_DIR,   exist_ok=True)


# ─────────────────────────────────────────────────────────────
# PART A: SCRAPE PRODUCT DATA
# Using requests + BeautifulSoup as specified in PDF
# Source: Fake Store API (free, no rate limiting, perfect for demo)
# In production: swap this with BeautifulSoup on Amazon/Flipkart
# ─────────────────────────────────────────────────────────────
def scrape_products_from_api():
    """
    Fetches products from Fake Store API.
    Returns a list of dicts with product info.
    This is where BeautifulSoup would be used on a real shopping site.
    """
    print("\n" + "="*60)
    print("PHASE 1A: SCRAPING PRODUCTS")
    print("="*60)

    all_products = []

    # ── Source 1: Fake Store API (20 products) ──────────────────
    print("\n[1/3] Fetching from Fake Store API...")
    try:
        resp = requests.get(
            "https://fakestoreapi.com/products",
            timeout=15
        )
        resp.raise_for_status()
        items = resp.json()

        for item in items:
            all_products.append({
                "name":        item["title"],
                "category":    item["category"].replace("'", ""),
                "description": item["description"],
                "price":       item["price"],
                "image_url":   item["image"],
                "source":      "fakestoreapi"
            })
        print(f"  Got {len(items)} products from Fake Store API")

    except Exception as e:
        print(f"  Warning: Fake Store API failed: {e}")

    # ── Source 2: DummyJSON API (100 more products) ─────────────
    print("\n[2/3] Fetching from DummyJSON API...")
    try:
        resp = requests.get(
            "https://dummyjson.com/products?limit=100",
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        for item in data["products"]:
            # Get first available image
            img_url = item["thumbnail"] if item.get("thumbnail") else ""

            all_products.append({
                "name":        item["title"],
                "category":    item["category"],
                "description": item["description"],
                "price":       item["price"],
                "image_url":   img_url,
                "source":      "dummyjson"
            })
        print(f"  Got {len(data['products'])} products from DummyJSON")

    except Exception as e:
        print(f"  Warning: DummyJSON API failed: {e}")

    # ── Source 3: Open Food Facts (extra variety) ────────────────
    print("\n[3/3] Fetching from Open Products Data...")
    try:
        resp = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl"
            "?action=process&json=1&page_size=20&fields="
            "product_name,categories,image_url",
            timeout=15
        )
        data = resp.json()
        count = 0
        for item in data.get("products", []):
            name = item.get("product_name", "").strip()
            if not name:
                continue
            all_products.append({
                "name":        name,
                "category":    "food & grocery",
                "description": f"Food product: {name}. "
                               f"Category: {item.get('categories','')[:100]}",
                "price":       round(5 + len(name) % 20, 2),
                "image_url":   item.get("image_url", ""),
                "source":      "openfoodfacts"
            })
            count += 1
        print(f"  Got {count} products from Open Food Facts")

    except Exception as e:
        print(f"  Warning: Open Food Facts failed: {e}")

    print(f"\n✅ Total raw products collected: {len(all_products)}")
    return all_products


# ─────────────────────────────────────────────────────────────
# PART B: DOWNLOAD IMAGES
# Using Pillow (PIL) to open, resize and save images
# Images saved as: images/PROD_001.jpg, images/PROD_002.jpg ...
# ─────────────────────────────────────────────────────────────
def download_image(url: str, save_path: str) -> bool:
    """
    Downloads one image from URL, resizes it to 224x224,
    saves as JPEG. Returns True if successful.
    Uses: requests (download), Pillow (resize + save)
    """
    if not url or not url.startswith("http"):
        return False
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=10, headers=headers)
        resp.raise_for_status()

        # Use Pillow to open, resize and save
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img = img.resize((224, 224), Image.LANCZOS)
        img.save(save_path, "JPEG", quality=85)
        return True

    except Exception:
        return False


def download_all_images(products: list) -> list:
    """
    Downloads images for all products.
    Adds 'image_path' column to each product dict.
    Skips products whose images fail to download.
    """
    print("\n" + "="*60)
    print("PHASE 1B: DOWNLOADING IMAGES")
    print("="*60)

    results = []
    success = 0

    for i, product in enumerate(tqdm(products, desc="Downloading images")):
        product_id  = f"PROD_{i+1:03d}"
        image_path  = f"{IMAGES_DIR}/{product_id}.jpg"

        downloaded = download_image(product["image_url"], image_path)

        if downloaded:
            product["product_id"] = product_id
            product["image_path"] = image_path
            results.append(product)
            success += 1
        else:
            # Skip products with no downloadable image
            pass

        # Be polite — small delay between downloads
        time.sleep(0.1)

    print(f"\n✅ Successfully downloaded {success}/{len(products)} images")
    print(f"   Images saved in: {IMAGES_DIR}/")
    return results


# ─────────────────────────────────────────────────────────────
# PART C: GENERATE LOST ITEM DESCRIPTIONS
# Using Ollama (llama3.2) — runs fully locally on your machine
# This is the "local LLM" the PDF mentions
# ─────────────────────────────────────────────────────────────
def generate_lost_description_ollama(product: dict) -> str:
    """
    Calls Ollama (llama3.2) to generate a realistic lost item
    description from the product's real description.
    
    Example:
      Input:  "Sony WH-1000XM5 - noise cancelling headphones..."
      Output: "I lost my black wireless headphones near the library.
               They have a silver band and came in a hard case."
    """
    prompt = f"""A college student lost this item on campus.
Write a realistic 2-sentence lost item report as if the student
is describing what they lost. Sound natural and slightly vague
(like a real person would describe it, not a product listing).

Product: {product['name']}
Category: {product['category']}
Description: {product['description'][:200]}

Write ONLY the lost item description. No intro, no extra text."""

    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"].strip()

    except Exception as e:
        # Fallback if Ollama is not running
        return (f"I lost my {product['name']} somewhere on campus. "
                f"It's a {product['category']} item and I really need it back.")


def generate_all_descriptions(products: list) -> list:
    """
    Generates lost item descriptions for all products.
    Adds 'lost_description' column.
    """
    print("\n" + "="*60)
    print("PHASE 1C: GENERATING LOST ITEM DESCRIPTIONS (Ollama)")
    print("="*60)
    print("Make sure Ollama is running: ollama serve")
    print("And llama3.2 is pulled: ollama pull llama3.2\n")

    for product in tqdm(products, desc="Generating descriptions"):
        product["lost_description"] = generate_lost_description_ollama(product)
        time.sleep(0.2)   # small pause between API calls

    print(f"\n✅ Generated descriptions for {len(products)} products")
    return products


# ─────────────────────────────────────────────────────────────
# PART D: SAVE TO CSV
# Using pandas as specified in PDF
# ─────────────────────────────────────────────────────────────
def save_to_csv(products: list):
    """Saves the product list to data/scraped_products.csv"""
    df = pd.DataFrame(products)

    # Select and order the columns we need
    columns = [
        "product_id", "name", "category", "description",
        "lost_description", "price", "image_url", "image_path", "source"
    ]
    # Only keep columns that exist
    columns = [c for c in columns if c in df.columns]
    df = df[columns]

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Saved {len(df)} products to {OUTPUT_CSV}")
    print(f"\nColumn overview:")
    print(df.dtypes.to_string())
    print(f"\nSample row:")
    print(df.iloc[0][["name","category","lost_description"]].to_string())
    return df


# ─────────────────────────────────────────────────────────────
# MAIN — run all parts in sequence
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Step 1: Scrape product data from APIs
    raw_products = scrape_products_from_api()

    # Step 2: Download images (removes products with broken images)
    products_with_images = download_all_images(raw_products)

    # Step 3: Generate lost item descriptions using Ollama
    products_complete = generate_all_descriptions(products_with_images)

    # Step 4: Save to CSV
    df = save_to_csv(products_complete)

    print("\n" + "="*60)
    print("PHASE 1 COMPLETE!")
    print(f"  Products:  {len(df)}")
    print(f"  CSV:       {OUTPUT_CSV}")
    print(f"  Images:    {IMAGES_DIR}/")
    print("="*60)