import pandas as pd
import requests
import time
from tqdm import tqdm
import math

# --- Configuration ---
API_KEY = "9e679601ed5bca8322fc8c59bbf87412"  # ❗ PASTE YOUR API KEY HERE
OUTPUT_CSV = 'dataset/tamil_movies_new.csv'
BASE_URL = "https://api.themoviedb.org/3"
MOVIES_TO_FETCH = 500
MAX_PAGES_PER_YEAR = 50  # Safety limit

# --- Session and Robust Request Function ---
session = requests.Session()
session.headers.update({
    "User-Agent": "MyMovieDataProject/1.0"
})


def make_api_request_with_retry(url, params):
    """Makes an API request with a retry mechanism for network errors."""
    max_retries = 3
    backoff_factor = 2

    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\nRequest failed: {e}. Attempt {attempt + 1} of {max_retries}.")
            if attempt + 1 == max_retries:
                print("Max retries reached. Failing this request.")
                return None
            time.sleep(backoff_factor * (attempt + 1))
    return None


# --- MODIFIED Main Fetching Function ---
def fetch_theatrical_tamil_movies(num_movies_total):
    """
    Fetches a balanced list of popular Tamil theatrical releases from
    specific years, skipping 2020.
    """
    all_movies = []
    # MODIFICATION: Define the specific years to process
    years_to_process = [y for y in range(2018, 2026) if y != 2020]
    num_years = len(years_to_process)

    if num_years == 0:
        print("Error: No years to process.")
        return []

    # MODIFICATION: Calculate how many movies to get per year for a balanced set
    base_movies_per_year = num_movies_total // num_years
    remainder = num_movies_total % num_years

    # Create a dictionary of how many movies to fetch for each year
    # This distributes the 'remainder' (e.g., 500 / 9 = 55 with 5 remainder)
    # So 5 years will get 56 movies, and 4 years will get 55. Total = 500.
    target_counts = {}
    for i, year in enumerate(years_to_process):
        target_counts[year] = base_movies_per_year
        if i < remainder:
            target_counts[year] += 1

    print(f"Targeting {num_movies_total} movies across {num_years} years ({years_to_process}).")
    print(f"Yearly targets: {target_counts}")

    # Outer loop for each year (now with tqdm)
    for year in tqdm(years_to_process, desc="Processing Years"):
        movies_found_this_year = 0
        target_for_this_year = target_counts[year]

        print(f"\n--- Processing Year: {year} (Target: {target_for_this_year}) ---")

        # Inner loop for pages within that year
        for page_num in range(1, MAX_PAGES_PER_YEAR + 1):
            params = {
                'api_key': API_KEY,
                'language': 'en-US',
                'sort_by': 'popularity.desc',
                'with_original_language': 'ta',
                'with_release_type': '3',  # Theatrical release
                'page': page_num,
                'primary_release_date.gte': f'{year}-01-01',
                'primary_release_date.lte': f'{year}-12-31'
            }

            data = make_api_request_with_retry(f"{BASE_URL}/discover/movie", params)

            if not data or not data.get('results'):
                print(f"No more results for {year} after page {page_num - 1}.")
                break  # No more results for this year

            for movie in data['results']:
                all_movies.append({
                    'Title': movie['title'],
                    'Year': movie['release_date'][:4] if movie.get('release_date') else year
                })
                movies_found_this_year += 1

                # MODIFICATION: Stop when we hit the target for THIS YEAR
                if movies_found_this_year >= target_for_this_year:
                    break

            # This breaks the inner (page) loop
            if movies_found_this_year >= target_for_this_year:
                print(f"Collected target of {movies_found_this_year} movies for {year}.")
                break

            if page_num == MAX_PAGES_PER_YEAR:
                print(f"Warning: Hit max pages ({MAX_PAGES_PER_YEAR}) for {year}. "
                      f"Only found {movies_found_this_year}/{target_for_this_year} movies.")

            time.sleep(0.5)  # Be nice to the API

    print(f"\nCollected a total of {len(all_movies)} movies.")
    return all_movies


# --- Main Script ---
if __name__ == "__main__":
    print("Starting script to fetch Tamil theatrical movie releases...")

    tamil_movies = fetch_theatrical_tamil_movies(MOVIES_TO_FETCH)

    if tamil_movies:
        df = pd.DataFrame(tamil_movies)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Success! Saved {len(df)} Tamil movies to '{OUTPUT_CSV}'.")
    else:
        print("\nCould not fetch any movies. Please check your API key and network connection.")