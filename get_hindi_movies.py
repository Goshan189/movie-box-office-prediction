import pandas as pd
import requests
import time

# --- Configuration ---
API_KEY = "9e679601ed5bca8322fc8c59bbf87412"  # ❗ PASTE YOUR API KEY HERE
INPUT_CSV = 'dataset/hindi_movies_boxoffice.csv'
OUTPUT_CSV = 'dataset/hindi_movies_boxoffice2.csv'
BASE_URL = "https://api.themoviedb.org/3"

# --- NEW: Session and Robust Request Function ---
session = requests.Session()
session.headers.update({
    "User-Agent": "MyMovieDataProject/1.0"
})


def make_api_request_with_retry(url, params):
    """Makes an API request with a retry mechanism for network errors."""
    max_retries = 3
    backoff_factor = 2  # Wait 2s, then 4s, then 6s

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


# --- MODIFIED: Fetch function now uses the retry logic ---
def fetch_theatrical_movies_tmdb():
    """Fetches Hindi theatrical releases from 2016-2025 using the TMDb API."""
    all_movies = []
    # Loop through pages of API results
    for page_num in range(1, 11):  # Fetches up to 10 pages (200 movies)
        print(f"Fetching page {page_num} from TMDb...")
        params = {
            'api_key': API_KEY,
            'language': 'en-US',
            'with_original_language': 'hi',
            'primary_release_date.gte': '2016-01-01',
            'primary_release_date.lte': '2025-12-31',
            'with_release_type': '3',  # Type 3 is Theatrical Release
            'page': page_num
        }

        # Use our new robust function
        data = make_api_request_with_retry(f"{BASE_URL}/discover/movie", params)

        if not data or not data.get('results'):
            print("Stopping: No more results or an unrecoverable error occurred.")
            break

        results = data['results']
        for movie in results:
            all_movies.append({
                'Title': movie['title'],
                'Year': movie['release_date'][:4] if movie.get('release_date') else None,
                'Language': 'Hindi'
            })
        time.sleep(0.5)  # Be polite between successful page fetches
    return all_movies


# --- Main Automation Script (Unchanged) ---
if __name__ == "__main__":
    df_existing = pd.read_csv(INPUT_CSV,encoding='latin1')
    df_existing.columns = df_existing.columns.str.strip()
    existing_titles = set(df_existing['Title'])
    print(f"Loaded {len(existing_titles)} existing movies.")

    tmdb_movies = fetch_theatrical_movies_tmdb()

    new_movies_to_add = []
    if tmdb_movies:
        for movie in tmdb_movies:
            if movie['Title'] not in existing_titles:
                new_movies_to_add.append(movie)
                existing_titles.add(movie['Title'])

    if new_movies_to_add:
        df_new = pd.DataFrame(new_movies_to_add)
        df_augmented = pd.concat([df_existing, df_new], ignore_index=True)
        df_augmented.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Success! Added {len(new_movies_to_add)} new movies from TMDb.")
        print(f"New, augmented dataset saved to '{OUTPUT_CSV}'.")
    else:
        print("\nNo new movies found to add from TMDb.")