import pandas as pd
import requests
import time
import re
from bs4 import BeautifulSoup
from tqdm import tqdm

# --- Configuration ---
INPUT_CSV = 'dataset/tamil_movies_2.csv'  # From your previous script
OUTPUT_CSV = 'dataset/tamil_movies_boxoffice.csv'
REQUEST_DELAY_SECONDS = 7  # Seconds to wait between Google searches

# --- Session and Headers ---
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
})


def search_google_for_sacnilk_url(movie_title, year):
    """
    Searches Google to find the Sacnilk.com box office page for a movie.
    """
    search_query = f'"{movie_title}" {year} box office collection sacnilk'
    search_url = "https://www.google.com/search"

    try:
        response = session.get(search_url, params={'q': search_query}, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        for link in soup.find_all('a'):
            href = link.get('href')
            if href and "sacnilk.com/mw/" in href and "http" in href:
                clean_url = href.split('url=')[1].split('&')[0]
                # Make sure it's a box office page
                if 'box_office' in clean_url.lower():
                    return clean_url

    except requests.exceptions.RequestException as e:
        print(f"\nError searching Google for {movie_title}: {e}")
        return None

    return None


def clean_collection_value(value_str):
    """
    Cleans a string like '₹ 10.5 Cr' into a float '10.5'.
    """
    if not isinstance(value_str, str):
        return None

    # Use regex to find the first number (integer or decimal)
    match = re.search(r'[\d\.]+', value_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


# --- MODIFIED: More Robust Scraping Function ---
def scrape_sacnilk_page(url):
    """
    Scrapes the target Sacnilk page for the box office table.
    Returns Day 1 Tamil Nadu Gross in Crores.

    This version is more robust and tries multiple ways to find 'Day 1'.
    """
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        tables = pd.read_html(response.text)

        if not tables:
            return None

        for df in tables:
            # Make a copy to avoid SettingWithCopyWarning
            df = df.copy()

            # Normalize column names
            df.columns = [str(col).lower() for col in df.columns]

            day_col = None
            tn_col = None

            for col in df.columns:
                if 'day' in col:
                    day_col = col
                if 'tamil nadu' in col and 'gross' in col:
                    tn_col = col

            if day_col and tn_col:
                # Standardize the 'day' column for matching
                df[day_col] = df[day_col].astype(str).str.lower().str.strip()

                day_1_row = None

                # --- Attempt 1: Find rows that contain "day 1" ---
                day_1_rows = df[df[day_col].str.contains('day 1', case=False, na=False)]
                if not day_1_rows.empty:
                    day_1_row = day_1_rows.iloc[0]

                # --- Attempt 2: If no match, find rows that are exactly "1" ---
                if day_1_row is None:
                    day_1_rows = df[df[day_col] == '1']
                    if not day_1_rows.empty:
                        day_1_row = day_1_rows.iloc[0]

                # --- Attempt 3: If no match, find rows that *start with* "1" (catches "1 (Fri)") ---
                if day_1_row is None:
                    day_1_rows = df[df[day_col].str.startswith('1', na=False)]
                    if not day_1_rows.empty:
                        day_1_row = day_1_rows.iloc[0]

                # If we found a 'Day 1' row by any method...
                if day_1_row is not None:
                    raw_value = day_1_row[tn_col]
                    cleaned_value = clean_collection_value(raw_value)
                    if cleaned_value is not None:
                        return cleaned_value  # Success!

    except requests.exceptions.RequestException as e:
        print(f"\nError scraping Sacnilk page {url}: {e}")
        return None
    except Exception as e:
        print(f"\nError parsing table on {url}: {e}")
        return None

    return None  # We looped all tables and found nothing


# --- Main Script (with Debugging) ---
if __name__ == "__main__":
    try:
        movie_df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{INPUT_CSV}'.")
        print("Please run your first script to generate this file.")
        exit()

    results = []

    print(f"Starting to scrape Day 1 TN Gross for {len(movie_df)} movies...")
    print(f"WARNING: This will be SLOW ({REQUEST_DELAY_SECONDS} sec per movie) to avoid IP bans.")

    for index, row in tqdm(movie_df.iterrows(), total=movie_df.shape[0]):
        title = row['Title']
        year = row['Year']

        # 1. Find the URL
        sacnilk_url = search_google_for_sacnilk_url(title, year)

        day_1_tn_gross_cr = None
        if sacnilk_url:
            # 2. Scrape the URL
            day_1_tn_gross_cr = scrape_sacnilk_page(sacnilk_url)

        # --- ADDED: Debug message for failed scrapes ---
        if day_1_tn_gross_cr is None and sacnilk_url:
            print(f"\n[Debug] No data found for '{title}'. Check URL: {sacnilk_url}")

        results.append({
            'Title': title,
            'Year': year,
            'Sacnilk_URL': sacnilk_url,
            'Day_1_TN_Gross_Cr': day_1_tn_gross_cr
        })

        # CRITICAL: Wait between requests
        time.sleep(REQUEST_DELAY_SECONDS)

    # --- Save Results ---
    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_CSV, index=False)

    found_count = output_df['Day_1_TN_Gross_Cr'].notna().sum()
    total_count = len(output_df)
    percent_found = (found_count / total_count) * 100

    print(f"\n✅ Success! Saved data to '{OUTPUT_CSV}'.")
    print(f"--- Found data for {found_count} out of {total_count} movies ({percent_found:.1f}%) ---")