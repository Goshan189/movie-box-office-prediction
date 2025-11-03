import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from tqdm import tqdm

# --- Configuration ---
INPUT_CSV = 'dataset/hindi_movies_boxoffice.csv'
OUTPUT_CSV = 'dataset/hindi_movies_features.csv'
BASE_URL = 'https://www.bollywoodhungama.com'


# --- Helper Functions ---

def create_slug(title):
    """Converts a movie title into a URL-friendly 'slug'."""
    slug = title.lower()
    slug = re.sub(r'\(.*\)', '', slug).strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug


def parse_crew_wrapper(soup):
    """Extracts data from the key-value list in the crew wrapper."""
    details = {}
    crew_wrapper = soup.find('div', class_='crew-wrapper')
    if not crew_wrapper:
        return details

    # Find all list items (li) in the crew wrapper
    list_items = crew_wrapper.find_all('li')
    for item in list_items:
        header = item.find('h4', class_='name')
        if header:
            key = header.text.strip().replace(':', '')
            # The data is in a <ul> tag within the same <li>
            value_list = item.find('ul', class_='no-bullet')
            if value_list:
                # Join all list items with a comma
                values = [v.text.strip() for v in value_list.find_all(['li', 'a'])]
                details[key] = ', '.join(values)
    return details


# --- Main Scraping Function ---
def scrape_bh_details(movie_slug):
    """Scrapes all required details from a movie's cast page."""
    url = f"{BASE_URL}/movie/{movie_slug}/cast/"
    headers = {'User-Agent': 'MyMovieDataScraper/1.0'}

    scraped_data = {}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Extract details from the crew wrapper ---
        crew_data = parse_crew_wrapper(soup)
        scraped_data['Banner'] = crew_data.get('Banner')
        scraped_data['Release Date'] = crew_data.get('Release Date')
        scraped_data['Genre'] = crew_data.get('Genre')
        scraped_data['Director'] = crew_data.get('Director')

        # --- THIS IS THE MODIFIED SECTION ---
        censor_details = crew_data.get('Censor Details')
        if censor_details:
            total_minutes = 0
            # Find the hour part (e.g., "2h")
            hours_match = re.search(r'(\d+)\s*h', censor_details)
            if hours_match:
                total_minutes += int(hours_match.group(1)) * 60

            # Find the minute part (e.g., "38mins")
            minutes_match = re.search(r'(\d+)\s*min', censor_details)
            if minutes_match:
                total_minutes += int(minutes_match.group(1))

            # Assign the calculated total if it's greater than 0
            scraped_data['Runtime (min)'] = total_minutes if total_minutes > 0 else None

            # The certification logic remains the same
            cert_match = re.search(r'\((\w\/?\w?\+?)\)', censor_details)
            scraped_data['Certification'] = cert_match.group(1) if cert_match else None
        # --- END OF MODIFIED SECTION ---

        # --- Extract the first 3 cast members ---
        cast_section = soup.find('div', id='load-more-content')
        if cast_section:
            cast_names = [name.text.split('...')[0].strip() for name in cast_section.find_all('h4', class_='name')]
            scraped_data['Cast'] = ', '.join(cast_names[:3])

        return scraped_data

    except requests.exceptions.RequestException:
        return {}

# --- Main Script ---
if __name__ == "__main__":
    df = pd.read_csv(INPUT_CSV)
    df.columns = df.columns.str.strip()

    # Define the new columns to add
    new_cols = ['Banner', 'Release Date', 'Genre', 'Director', 'Runtime_mins', 'Certification', 'Cast']
    for col in new_cols:
        if col not in df.columns:
            df[col] = pd.NA

    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        title = row['Title']
        slug = create_slug(title)

        details = scrape_bh_details(slug)

        if details:
            for key, value in details.items():
                df.loc[index, key] = value

        time.sleep(1)  # Be polite to the server

        if (index + 1) % 50 == 0:
            df.to_csv(OUTPUT_CSV, index=False)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Scraping complete! Data saved to '{OUTPUT_CSV}'.")