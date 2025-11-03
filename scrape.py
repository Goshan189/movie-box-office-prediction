import requests
from bs4 import BeautifulSoup
from io import StringIO
import pandas as pd
import random
import time


def fetch_movies(year):
    url = 'https://en.wikipedia.org/w/api.php'
    params = {
        'action': 'parse',
        'page': f'List_of_Hindi_films_of_{year}',
        'format': 'json',
        'prop': 'text'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        print(f"[{year}] Failed to fetch data. Status code: {response.status_code}")
        return []

    try:
        html_content = response.json()['parse']['text']['*']
    except Exception as e:
        print(f"[{year}] JSON decode error or missing data: {e}")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table', {'class': 'wikitable'})


    movies = []
    for table in tables:
        df = pd.read_html(StringIO(str(table)))[0]
        if 'Title' in df.columns :
            for index, row in df.iterrows():
                title = row['Title']
                movies.append({'Title': title, 'Year': year, 'Language': 'Hindi'})

    print(f"[{year}] Collected {len(movies)} movies.")
    return movies


all_movies = []
for year in range(2016, 2026):
    if year==2020:
        continue
    movies = fetch_movies(year)
    all_movies.extend(movies)
    time.sleep(random.randint(1,3))  # To be polite to Wikipedia API

print(f"\nTotal movies fetched: {len(all_movies)}")

# Random sample of ~1000 movies
sample_size = min(600, len(all_movies))
sampled_movies = random.sample(all_movies, sample_size)

# Save to CSV
df = pd.DataFrame(sampled_movies)
df.to_csv('hindi_movies2.csv',mode='a', header=True,index=False)
print(f"\nSaved {sample_size} movies to 'hindi_movies2.csv'")
print(df.head())