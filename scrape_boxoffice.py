'''import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from tqdm import tqdm

# --- Configuration ---
INPUT_CSV = 'dataset/tamil_movies_2.csv'
OUTPUT_CSV = 'dataset/tamil_movies_boxoffice.csv'
BASE_URL = 'https://www.bollywoodhungama.com'


# --- Your scraping function (logic unchanged) ---
def find_and_scrape_day1(movie_title):
    movie_title=movie_title.lower()
    movie_title=movie_title.replace(':','-')

    movie_title = re.sub(r'-\s+', '-', movie_title)

    movie_title=movie_title.replace(' ','-')

    headers = {'User-Agent': 'MyMovieDataScraper/1.0 (for academic research)'}
    amount_in_number = None  # default if not found

    try:
        search_url = f"{BASE_URL}/movie/{movie_title}/box-office/"
        search_response = requests.get(search_url, headers=headers, timeout=30)
        if search_response.status_code != 200:
            print(f'Page not found: {movie_title}')

            return None

        search_soup = BeautifulSoup(search_response.text, 'html.parser')

        # --- STEP 2: Navigate to the movie's box office page ---
        time.sleep(2)  # polite pause
        boxoffice_page = requests.get(search_url, headers=headers, timeout=30)
        if boxoffice_page.status_code != 200:
            return None

        movie_soup = BeautifulSoup(boxoffice_page.text, 'html.parser')
        table = movie_soup.find('table', class_='tablesaw tablesaw-swipe')

        amount = ''
        if table:
            first_data_row = table.tbody.find('tr')
            if first_data_row:
                cells = first_data_row.find_all('td')
                if len(cells) > 1:
                    collection_cell = cells[1]
                    amount = collection_cell.text.strip()

        match = re.search(r'\d[\d\.]*', amount)
        if match:
            amount_in_number = float(match.group(0))

        return amount_in_number

    except requests.exceptions.RequestException as e:
        print(f"--> A network error occurred for '{movie_title}': {e}")
        return None


# --- Main: read CSV, scrape, and save ---
df = pd.read_csv(INPUT_CSV,encoding='latin1')

# Add a new column for Day 1 collection
df['Day1_collection_cr'] = None
df.columns = df.columns.str.strip()
# Loop over movies with a progress bar
for idx, row in tqdm(df.iterrows(), total=len(df)):

    movie_name = row['Title'] # assuming your CSV has a column named 'Movie'
    day1_amount = find_and_scrape_day1(movie_name)
    df.at[idx, 'Day1_collection_cr'] = day1_amount
    time.sleep(1)  # polite delay between requests

# Save the enriched CSV
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Saved updated CSV with Day1 collection to '{OUTPUT_CSV}'")'''

#ENG MOVIES
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from tqdm import tqdm
from urllib.parse import quote_plus

# --- Configuration ---
INPUT_CSV = 'dataset/english_movies_dates.csv'
OUTPUT_CSV = 'dataset/english_movies_collection.csv'
COLUMN_NAME = 'day1_collection_cr'
BH_BASE_URL = 'https://www.bollywoodhungama.com'

# --- Session and Helper Functions ---
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
})


def create_bh_slug_english(title):
    """
    Converts a movie title into the specific Bollywood Hungama
    URL slug format for English movies.
    e.g., "Mission: Impossible Fallout" -> "mission-impossible-fallout-english"
    """
    slug = title.lower()
    # Remove things like (2018)
    slug = re.sub(r'\(.*\)', '', slug).strip()
    # Keep letters, numbers, spaces, colons, and existing hyphens
    slug = re.sub(r'[^a-z0-9\s:-]', '', slug)
    # Replace one or more colons or spaces with a single hyphen
    slug = re.sub(r'[:\s]+', '-', slug)
    # Append the required suffix
    slug = f"{slug}-english"
    return slug


def scrape_bh_day1_english(movie_slug):
    """
    Scrapes the Day 1 or Opening Day collection from the BH page.
    """
    try:
        url = f"{BH_BASE_URL}/movie/{movie_slug}/box-office/"
        print(f"\nAttempting to fetch: {url}")

        response = session.get(url, timeout=15)
        # Check for 404 Not Found
        if response.status_code != 200:
            print(f"  -> Page not found (404) for slug: {movie_slug}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the correct box office table
        table = soup.find('table', class_='table table-bordered table-striped')

        if not table:
            # Fallback in case the class changes slightly
            table = soup.find('div', class_='table-responsive').find('table')
            if not table:
                print(f"  -> Found page, but no box office table for: {movie_slug}")
                return None

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 1:
                period = cells[0].text.strip()

                # Check for EITHER "Day 1" OR "Opening Day"
                if period == "Day 1" or period == "Opening Day":
                    collection_str = cells[1].text.strip()
                    # Extract the number (e.g., from "Rs. 36.50 cr.")
                    value_match = re.search(r'[\d\.]+', collection_str)
                    if value_match:
                        value = float(value_match.group(0))
                        print(f"  -> SUCCESS: Found '{period}' collection: {value} Cr")
                        return value

        print(f"  -> Found table, but no 'Day 1' or 'Opening Day' row for: {movie_slug}")
        return None

    except Exception as e:
        print(f"\nScraping failed for '{movie_slug}': {e}")
        return None


# --- Main Script Execution ---
if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV,encoding='latin1')


    if COLUMN_NAME not in df.columns:
        df[COLUMN_NAME] = pd.NA

    print(f"Loaded {len(df)} movies. Starting to fetch Day 1 collections from Bollywood Hungama...")

    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        # Only scrape if the cell is currently empty
        if pd.isna(df.loc[index, COLUMN_NAME]):
            title = row['Title']

            # Create the specific slug using your new logic
            slug = create_bh_slug_english(title)

            collection = scrape_bh_day1_english(slug)

            if collection is not None:
                df.loc[index, COLUMN_NAME] = collection

            time.sleep(2)  # Be polite

        # Save progress every 25 movies
        if (index + 1) % 25 == 0:
            df.to_csv(OUTPUT_CSV, index=False)

    # Final save
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\n✅✅✅ Task Complete! ✅✅✅")
    print(f"Scraping finished. The new data is saved in '{OUTPUT_CSV}'.")