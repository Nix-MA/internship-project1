# phase2_clean.py
# Save in: lost_found_reunion/phase2_clean.py
#
# WHAT THIS FILE DOES:
# 1. Loads data/scraped_products.csv
# 2. Removes duplicates and rows with missing data
# 3. Verifies every image file exists and opens correctly
# 4. Standardises category names
# 5. Creates a combined search_text field
# 6. Saves to data/lost_found_dataset_cleaned.csv
#
# TOOLS USED: pandas, Pillow

import pandas as pd
import os
from PIL import Image

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
INPUT_CSV  = "data/scraped_products.csv"
OUTPUT_CSV = "data/lost_found_dataset_cleaned.csv"


# ─────────────────────────────────────────────────────────────
# STEP 1: Load the raw data
# ─────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    print("\n" + "="*60)
    print("PHASE 2: DATA CLEANING")
    print("="*60)

    df = pd.read_csv(INPUT_CSV)
    print(f"\n✅ Loaded {len(df)} rows from {INPUT_CSV}")
    print(f"   Columns: {list(df.columns)}")
    return df


# ─────────────────────────────────────────────────────────────
# STEP 2: Remove duplicates
# ─────────────────────────────────────────────────────────────
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    # Remove products with identical names (keep first)
    df = df.drop_duplicates(subset=["name"], keep="first")

    removed = before - len(df)
    print(f"\n[Duplicates] Removed {removed} duplicate rows → {len(df)} remain")
    return df


# ─────────────────────────────────────────────────────────────
# STEP 3: Drop rows with missing critical fields
# ─────────────────────────────────────────────────────────────
def drop_missing(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # These columns must have values — drop rows where they are empty
    required = ["name", "description", "lost_description",
                "category", "image_path"]
    df = df.dropna(subset=required)

    # Also drop rows where the text fields are empty strings
    for col in ["name", "description", "lost_description"]:
        df = df[df[col].str.strip().str.len() > 3]

    removed = before - len(df)
    print(f"[Missing]    Removed {removed} rows with missing fields → {len(df)} remain")
    return df


# ─────────────────────────────────────────────────────────────
# STEP 4: Verify images exist and are valid using Pillow
# ─────────────────────────────────────────────────────────────
def verify_images(df: pd.DataFrame) -> pd.DataFrame:
    """
    Uses Pillow to open each image and verify it's not corrupted.
    Removes rows whose images are missing or broken.
    """
    before = len(df)
    valid_mask = []

    for path in df["image_path"]:
        if not os.path.exists(str(path)):
            valid_mask.append(False)
            continue
        try:
            with Image.open(path) as img:
                img.verify()   # Pillow checks if file is a valid image
            valid_mask.append(True)
        except Exception:
            valid_mask.append(False)

    df = df[valid_mask]
    removed = before - len(df)
    print(f"[Images]     Removed {removed} rows with broken images → {len(df)} remain")
    return df


# ─────────────────────────────────────────────────────────────
# STEP 5: Standardise category names
# ─────────────────────────────────────────────────────────────
def standardise_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps messy category names to clean consistent names.
    Example: "mens clothing" → "clothing"
    """
    category_map = {
        "men's clothing":        "clothing",
        "mens clothing":         "clothing",
        "women's clothing":      "clothing",
        "womens clothing":       "clothing",
        "jewelery":              "jewelry",
        "jewellery":             "jewelry",
        "electronics":           "electronics",
        "smartphones":           "electronics",
        "laptops":               "electronics",
        "tablets":               "electronics",
        "mobile-accessories":    "electronics",
        "sports":                "sports & fitness",
        "sports-accessories":    "sports & fitness",
        "mens-shoes":            "footwear",
        "womens-shoes":          "footwear",
        "mens-watches":          "watches & jewelry",
        "womens-watches":        "watches & jewelry",
        "womens-jewellery":      "jewelry",
        "sunglasses":            "accessories",
        "groceries":             "food & grocery",
        "home-decoration":       "home & decor",
        "furniture":             "home & decor",
        "tops":                  "clothing",
        "mens-shirts":           "clothing",
        "skin-care":             "personal care",
        "beauty":                "personal care",
        "fragrances":            "personal care",
        "food & grocery":        "food & grocery",
    }

    # Convert to lowercase first, then map
    df["category"] = (df["category"]
                      .str.lower()
                      .str.strip()
                      .replace(category_map))

    print(f"[Categories] Standardised → unique categories: "
          f"{df['category'].nunique()}")
    print(f"             {list(df['category'].unique())}")
    return df


# ─────────────────────────────────────────────────────────────
# STEP 6: Clean text — strip whitespace, fix encoding
# ─────────────────────────────────────────────────────────────
def clean_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    text_cols = ["name", "description", "lost_description", "category"]
    for col in text_cols:
        if col in df.columns:
            df[col] = (df[col]
                       .astype(str)
                       .str.strip()
                       .str.replace(r"\s+", " ", regex=True))
    print(f"[Text]       Cleaned whitespace in text columns")
    return df


# ─────────────────────────────────────────────────────────────
# STEP 7: Add item_id and search_text
# ─────────────────────────────────────────────────────────────
def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds:
      item_id     — unique ID like ITEM_0001
      search_text — combined text for embedding
                    (name + category + description + lost_description)
    """
    # Reset index so numbering is clean
    df = df.reset_index(drop=True)

    # Add item_id
    df["item_id"] = df.index.map(lambda i: f"ITEM_{i+1:04d}")

    # Create combined search text — this is what gets embedded
    # More text = better semantic search
    df["search_text"] = (
        df["name"]              + " " +
        df["category"]          + " " +
        df["description"]       + " " +
        df["lost_description"]
    ).str.lower().str.strip()

    # Add price bucket for UI display
    def price_bucket(p):
        try:
            p = float(p)
            if p < 20:   return "budget"
            if p < 100:  return "mid-range"
            if p < 300:  return "premium"
            return "luxury"
        except Exception:
            return "unknown"

    df["price_bucket"] = df["price"].apply(price_bucket)

    print(f"[Derived]    Added item_id, search_text, price_bucket columns")
    return df


# ─────────────────────────────────────────────────────────────
# STEP 8: Save cleaned data
# ─────────────────────────────────────────────────────────────
def save_clean_data(df: pd.DataFrame):
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Saved clean dataset → {OUTPUT_CSV}")
    print(f"   Total items: {len(df)}")
    print(f"\nCategory distribution:")
    print(df["category"].value_counts().to_string())
    return df


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = load_data()
    df = remove_duplicates(df)
    df = drop_missing(df)
    df = verify_images(df)
    df = standardise_categories(df)
    df = clean_text_fields(df)
    df = add_derived_columns(df)
    df = save_clean_data(df)

    print("\n" + "="*60)
    print("PHASE 2 COMPLETE!")
    print(f"  Clean CSV: {OUTPUT_CSV}")
    print(f"  Items:     {len(df)}")
    print("="*60)