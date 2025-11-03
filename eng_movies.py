'''import pandas as pd
import requests
import time
import math
from tqdm import tqdm

# --- Configuration ---
API_KEY = "9e679601ed5bca8322fc8c59bbf87412"
OUTPUT_CSV = 'dataset/english_movies.csv'
MOVIES_TO_FETCH = 600

# --- TMDb API Configuration ---
BASE_URL_TMDB = "https://api.themoviedb.org/3"
# Corresponds to: Action, Adventure, Animation, Fantasy, Sci-Fi, Thriller
GENRE_IDS_TO_FETCH = "28|12|16|14|878|53"

# A mapping to convert TMDb IDs to the exact genre names you want
GENRE_ID_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    14: "Fantasy",
    878: "Sci-Fi",
    53: "Thriller"
}

# --- Session and Robust Request Function ---
session = requests.Session()
session.headers.update({
    "User-Agent": "MyMovieDataProject/1.0 (for academic research)"
})


def make_api_request_with_retry(url, params):
    """Makes a TMDb API request with a retry mechanism."""
    max_retries = 3
    backoff_factor = 2
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\nAPI Request failed: {e}. Retrying...")
            time.sleep(backoff_factor * (attempt + 1))
    return None


# --- Main Movie Discovery Function ---
def discover_english_movies(num_movies_target):
    """
    Discovers a list of English movies that match the specified criteria.
    """

    print("--- Discovering 600 English movies released in India ---")

    movie_list_to_process = []
    # Years: 2018, 2019, 2021, 2022, 2023, 2024, 2025
    years_to_process = [y for y in range(2018, 2026) if y != 2020]

    # Calculate how many movies to get from each year for a balanced sample
    movies_per_year = math.ceil(num_movies_target / len(years_to_process))
    # Calculate how many pages to fetch (20 movies per page)
    pages_per_year = math.ceil(movies_per_year / 20)

    print(f"Targeting ~{movies_per_year} movies per year from: {years_to_process}")

    for year in years_to_process:
        print(f"\n--- Processing Year: {year} ---")
        movies_from_this_year = 0

        for page_num in tqdm(range(1, pages_per_year + 1)):
            params = {
                'api_key': API_KEY,
                'with_original_language': 'en',  # English movies
                'region': 'IN',  # Must have a release in India
                'with_genres': GENRE_IDS_TO_FETCH,  # From our allowed list
                'page': page_num,
                'primary_release_date.gte': f'{year}-01-01',  # Start of year
                'primary_release_date.lte': f'{year}-12-31',  # End of year
                'sort_by': 'popularity.desc'  # Get most popular ones first
            }

            data = make_api_request_with_retry(f"{BASE_URL_TMDB}/discover/movie", params)

            if not data or not data.get('results'):
                break  # No more results for this year

            for movie in data['results']:
                if movies_from_this_year < movies_per_year:
                    # Convert genre IDs to names
                    genre_names = [GENRE_ID_MAP[gid] for gid in movie['genre_ids'] if gid in GENRE_ID_MAP]

                    movie_list_to_process.append({
                        'Title': movie['title'],
                        'Year': year,
                        'Language': 'English',
                        'Genre': ', '.join(genre_names[:2])  # Get max 2 genres
                    })
                    movies_from_this_year += 1
                else:
                    break  # Reached quota for this year

            if movies_from_this_year >= movies_per_year:
                break  # Stop fetching pages, move to next year

            time.sleep(0.5)  # Be polite to the API

    print(f"\n--- Discovered {len(movie_list_to_process)} total movies. ---")

    # Trim the list to the exact number requested
    return pd.DataFrame(movie_list_to_process[:num_movies_target])


# --- Main Script Execution ---
if __name__ == "__main__":
    if API_KEY == "YOUR_TMDB_API_KEY_HERE":
        print("Error: Please paste your TMDb API key into the API_KEY variable.")
    else:
        df_movies = discover_english_movies(MOVIES_TO_FETCH)

        # Save the discovered list to a CSV
        df_movies.to_csv(OUTPUT_CSV, index=False)

        print(f"\n✅✅✅ Task Complete! ✅✅✅")
        print(f"Successfully discovered and saved {len(df_movies)} movies to '{OUTPUT_CSV}'.")'''

# get detaild
'''import pandas as pd
import requests
import time
from tqdm import tqdm
from datetime import datetime

# --- Configuration ---
API_KEY = "9e679601ed5bca8322fc8c59bbf87412"  # ❗ PASTE YOUR TMDB API KEY
INPUT_CSV = 'dataset/english_movies.csv'
OUTPUT_CSV = 'dataset/english_movies_details.csv'
BASE_URL_TMDB = "https://api.themoviedb.org/3"

# --- Session and Robust Request Function ---
session = requests.Session()
session.headers.update({
    "User-Agent": "MyMovieDataProject/1.0 (for academic research)"
})


def make_api_request_with_retry(url, params):
    """Makes a TMDb API request with a retry mechanism."""
    max_retries = 3
    backoff_factor = 2
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\nAPI Request failed: {e}. Retrying...")
            time.sleep(backoff_factor * (attempt + 1))
    return None


def fetch_movie_details(movie_title, movie_year):
    """
    Fetches all required details for a movie from TMDb
    by first searching for its ID.
    """
    details = {}

    # --- Step 1: Search for the movie to get its ID ---
    search_params = {
        'api_key': API_KEY,
        'query': movie_title,
        'primary_release_year': movie_year,
        'language': 'en-US',
        'with_original_language': 'en'
    }
    search_data = make_api_request_with_retry(f"{BASE_URL_TMDB}/search/movie", search_params)

    if not search_data or not search_data.get('results'):
        print(f"  -> Could not find movie ID for '{movie_title}' ({movie_year})")
        return {}  # Return empty dict if no movie found

    movie_id = search_data['results'][0]['id']

    # --- Step 2: Get all details using the ID ---
    details_params = {
        'api_key': API_KEY,
        'append_to_response': 'credits,release_dates'  # Get all data in one call
    }
    movie_data = make_api_request_with_retry(f"{BASE_URL_TMDB}/movie/{movie_id}", details_params)

    if not movie_data:
        return {}  # Return empty dict if details call fails

    # --- Step 3: Parse the details ---

    # Banner (max 2)
    banners = [p['name'] for p in movie_data.get('production_companies', [])]
    details['Banner'] = ', '.join(banners[:2])

    # Director (max 2)
    directors = [m['name'] for m in movie_data.get('credits', {}).get('crew', []) if m['job'] == 'Director']
    details['Director'] = ', '.join(directors[:2])

    # Cast (max 2)
    cast = [a['name'] for a in movie_data.get('credits', {}).get('cast', [])]
    details['Cast'] = ', '.join(cast[:2])

    # Runtime
    details['Runtime(mins)'] = movie_data.get('runtime')

    # Release date in India (DD-MM-YYYY)
    release_dates_results = movie_data.get('release_dates', {}).get('results', [])
    found_date = None
    for country in release_dates_results:
        if country['iso_3166_1'] == 'IN':
            for release in country['release_dates']:
                if release['type'] == 3:  # Type 3 is Theatrical
                    release_date_str = release['release_date'].split('T')[0]  # Get YYYY-MM-DD
                    dt_obj = datetime.strptime(release_date_str, '%Y-%m-%d')
                    found_date = dt_obj.strftime('%d-%m-%Y')  # Format to DD-MM-YYYY
                    break
            if found_date:
                break
    details['Release date (India)'] = found_date

    return details


# --- Main Script Execution ---
if __name__ == "__main__":
    if API_KEY == "YOUR_TMDB_API_KEY_HERE":
        print("Error: Please paste your TMDb API key into the API_KEY variable.")
    else:
        # Load the CSV of 602 movies
        df = pd.read_csv(INPUT_CSV)

        # Create new columns for the data we will fetch
        new_cols = ['Release date (India)', 'Runtime(mins)', 'Banner', 'Director', 'Cast']
        for col in new_cols:
            if col not in df.columns:
                df[col] = None

        print(f"Loaded {len(df)} movies. Starting to fetch details...")

        # Loop through each movie and fetch its details
        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            movie_details = fetch_movie_details(row['Title'], row['Year'])

            # Update the DataFrame with the new details
            if movie_details:
                for col, value in movie_details.items():
                    df.loc[index, col] = value

            time.sleep(0.5)  # Be polite to the API

        # Save the final, completed DataFrame to a new file
        df.to_csv(OUTPUT_CSV, index=False)

        print(f"\n✅✅✅ Task Complete! ✅✅✅")
        print(f"Successfully fetched details and saved to '{OUTPUT_CSV}'.")'''

import pandas as pd
import requests
import time
from tqdm import tqdm
from datetime import datetime

# --- Configuration ---
API_KEY = "9e679601ed5bca8322fc8c59bbf87412"  # ❗ PASTE YOUR TMDB API KEY
# Make sure this is your latest file with the 419 blanks
INPUT_CSV = 'dataset/english_movies_detail2.csv'
OUTPUT_CSV = 'dataset/english_movies_dates.csv'
BASE_URL_TMDB = "https://api.themoviedb.org/3"

# --- Session and Robust Request Function ---
session = requests.Session()
session.headers.update({
    "User-Agent": "MyMovieDataProject/1.0 (for academic research)"
})


def make_api_request_with_retry(url, params):
    max_retries = 3
    backoff_factor = 2
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Make the error non-silent
            print(f"\nAPI Request failed: {e}. Retrying...")
            time.sleep(backoff_factor * (attempt + 1))
    print(f"\nAPI Request FAILED permanently for {url}")
    return None


def fetch_release_date_diagnostic(movie_title, movie_year):
    """
    Fetches the release date with LOUD feedback on what it finds.
    """
    print(f"\n--- Processing: '{movie_title}' ({movie_year}) ---")

    # --- Step 1: Search for the movie to get its ID ---
    search_params = {
        'api_key': API_KEY, 'query': movie_title, 'primary_release_year': movie_year,
        'language': 'en-US', 'with_original_language': 'en'
    }
    search_data = make_api_request_with_retry(f"{BASE_URL_TMDB}/search/movie", search_params)

    if not search_data or not search_data.get('results'):
        print(f"  -> ❌ ERROR: Could not find this movie on TMDb. Cannot get ID.")
        return None

    movie_id = search_data['results'][0]['id']
    print(f"  -> Found Movie ID: {movie_id}")

    # --- Step 2: Get details using the ID ---
    details_params = {'api_key': API_KEY, 'append_to_response': 'release_dates'}
    movie_data = make_api_request_with_retry(f"{BASE_URL_TMDB}/movie/{movie_id}", details_params)

    if not movie_data:
        print(f"  -> ❌ ERROR: Found ID, but could not fetch details for this movie.")
        return None

    # --- Step 3: Parse the release date with fallback ---
    release_dates_results = movie_data.get('release_dates', {}).get('results', [])
    found_date_str = None

    # Attempt 1: Find the specific Indian Theatrical release
    for country in release_dates_results:
        if country['iso_3166_1'] == 'IN':
            for release in country['release_dates']:
                if release['type'] == 3:  # Type 3 is Theatrical
                    found_date_str = release['release_date'].split('T')[0]
                    break
            if found_date_str:
                break

    if found_date_str:
        print(f"  -> ✅ SUCCESS: Found specific Indian release date: {found_date_str}")
    else:
        # Attempt 2: Fallback to the primary release date
        print("  -> ⚠️ WARNING: Indian date not found. Attempting fallback...")
        found_date_str = movie_data.get('release_date')  # Main release date (YYYY-MM-DD)

        if found_date_str:
            print(f"  -> ✅ SUCCESS (Fallback): Found primary release date: {found_date_str}")
        else:
            print(f"  -> ❌ ERROR: Fallback failed. Primary release date is also blank in TMDb.")
            return None  # Exit if both are blank

    # Format the final date (if one was found) to DD-MM-YYYY
    try:
        dt_obj = datetime.strptime(found_date_str, '%Y-%m-%d')
        return dt_obj.strftime('%d-%m-%Y')
    except ValueError:
        print(f"  -> ❌ ERROR: Found date '{found_date_str}' but could not format it.")
        return None


# --- Main Script Execution ---
if __name__ == "__main__":
    if API_KEY == "YOUR_TMDB_API_KEY_HERE":
        print("Error: Please paste your TMDb API key into the API_KEY variable.")
    else:
        df = pd.read_csv(INPUT_CSV)

        print(f"Loaded {len(df)} movies. Checking for missing release dates...")

        # Find rows where the 'Release date (India)' column is empty
        missing_indices = df[df['Release date (India)'].isnull()].index

        print(f"Found {len(missing_indices)} movies with missing dates. Starting to fetch...")

        # Use .copy() to avoid SettingWithCopyWarning
        df_copy = df.copy()

        for index in tqdm(missing_indices):
            row = df_copy.loc[index]

            release_date = fetch_release_date_diagnostic(row['Title'], row['Year'])

            if release_date:
                df_copy.loc[index, 'Release date (India)'] = release_date

            time.sleep(0.5)  # Be polite to the API

        # Save the file
        df_copy.to_csv(OUTPUT_CSV, index=False)

        print(f"\n✅✅✅ Task Complete! ✅✅✅")
        print(f"Diagnostic run finished. Please check the new file: '{OUTPUT_CSV}'")