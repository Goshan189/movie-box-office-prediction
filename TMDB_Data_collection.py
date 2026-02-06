import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from tqdm import tqdm
from urllib.parse import quote_plus
from datetime import datetime
# --- Configuration ---

USD_TO_INR_RATE = 83.50



# --- Configuration ---
INPUT_CSV = 'dataset/hindi_movies_features_Completed.csv'
OUTPUT_CSV = 'dataset/hindi_movies_features_Completed2.csv'
API_KEY = "YOUR_TMDB_API_KEY_HERE"
BASE_URL_TMDB = "https://api.themoviedb.org/3"
GOOGLE_SEARCH_URL = "https://www.google.com/search?q="
BH_BASE_URL = 'https://www.bollywoodhungama.com'
# Session object for all requests
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
})


def create_bh_slug(title):
    slug = title.lower()
    slug = re.sub(r'\(.*\)', '', slug).strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug


def scrape_sacnilk_day1(movie_title, movie_year):
    # This function is the same as before
    try:
        query = f'"{movie_title} {movie_year} hindi movie box office collection site:sacnilk.com"'
        search_url = GOOGLE_SEARCH_URL + quote_plus(query)
        search_response = session.get(search_url, timeout=15)
        search_soup = BeautifulSoup(search_response.text, 'html.parser')
        result_tag = search_soup.find('a', href=re.compile(r'https://www.sacnilk.com/articles/'))
        if not result_tag: return None
        sacnilk_url = result_tag['href']
        if sacnilk_url.startswith('/url?q='):
            sacnilk_url = sacnilk_url.split('/url?q=')[1].split('&sa=')[0]
        time.sleep(1)
        sacnilk_response = session.get(sacnilk_url, timeout=15)
        sacnilk_soup = BeautifulSoup(sacnilk_response.text, 'html.parser')
        table = sacnilk_soup.find('table', class_=re.compile(r'kborder'))
        if not table: return None
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) > 1 and "Day 1" in cells[0].text.strip():
                collection_str = cells[1].text.strip()
                value_match = re.search(r'[\d\.]+', collection_str)
                if value_match: return float(value_match.group(0))
        return None
    except Exception:
        return None


def scrape_bh_day1(movie_title):
    """NEW: Scrapes Day 1 box office from Bollywood Hungama as a backup."""
    try:
        slug = create_bh_slug(movie_title)
        url = f"{BH_BASE_URL}/movie/{slug}/box-office/"
        response = session.get(url, timeout=15)
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table-box-office')
        if not table: return None

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 1 and "Day 1" in cells[0].text.strip():
                collection_str = cells[1].text.strip()
                value_match = re.search(r'[\d\.]+', collection_str)
                if value_match: return float(value_match.group(0))
        return None
    except Exception:
        return None


def get_day1_collection_multi_source(movie_title, movie_year):
    """
    NEW: Master function that tries multiple sources for box office data.
    """
    print(f"\nProcessing '{movie_title}'...")

    # --- Attempt 1: Sacnilk ---
    print("  -> Trying Sacnilk.com...")
    collection = scrape_sacnilk_day1(movie_title, movie_year)
    if collection is not None:
        print(f"  --> SUCCESS on Sacnilk: Found {collection} Cr")
        return collection

    # --- Attempt 2: Bollywood Hungama ---
    print("  -> Sacnilk failed. Trying BollywoodHungama.com...")
    time.sleep(1)  # Pause before trying the next site
    collection = scrape_bh_day1(movie_title)
    if collection is not None:
        print(f"  --> SUCCESS on Bollywood Hungama: Found {collection} Cr")
        return collection

    print("  -> All sources failed.")
    return None


# --- Main Script ---
if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV)
    df.columns = df.columns.str.strip()

    print(f"Loaded {len(df)} movies. Starting to fill missing box office values...")

    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        # Only process rows where the collection is missing
        if pd.isnull(row['Day1_collection_cr']):
            title = row['Title']
            year = row['Year']

            # Use the new multi-source function
            day1_collection = get_day1_collection_multi_source(title, year)

            if day1_collection is not None:
                df.loc[index, 'Day1_collection_cr'] = day1_collection

            # Be polite to the servers
            time.sleep(1)

        # Save progress every 10 movies processed
        if (index + 1) % 10 == 0:
            df.to_csv(OUTPUT_CSV, index=False)

    # Final save
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Task Complete! All missing values have been processed.")
    print(f"The completed file is saved as '{OUTPUT_CSV}'.")
