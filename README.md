# Movie Box Office Prediction

This project builds a **Day‑1 box office prediction** pipeline by collecting movie metadata and audience signals (YouTube trailer stats and sentiment), engineering features, and training classification models to predict opening performance.

## What was built

### 1) Data collection

- **Movie lists**: Scraped Hindi movie titles by year (2016–2025) from Wikipedia. See [scrape.py](scrape.py).
- **TMDb enrichment**: Pulled movie metadata like runtime, release date, production companies, and genres. See [TMDB_Data_collection.py](TMDB_Data_collection.py) and [get_hindi_movies.py](get_hindi_movies.py).
- **Box office (Day‑1)**: Scraped day‑1 collections from Bollywood Hungama and Sacnilk when missing. See [scrape_boxoffice.py](scrape_boxoffice.py) and [TMDB_Data_collection.py](TMDB_Data_collection.py).

### 2) Audience signals (YouTube)

- Trailer data was gathered using the YouTube API (view count, likes, comments) and sentiment from comments.
- These signals represent **audience interest around the trailer release** (e.g., within a week of release) and are used as predictive features.
- Resulting data is stored in [dataset/hindi_sentiment.csv](dataset/hindi_sentiment.csv).

> Note: Reddit signals were also considered as part of the audience‑interest feature idea, but YouTube trailer statistics and comment sentiment are the primary implemented signals in this pipeline.

### 3) Cleaning and preprocessing

- Missing values and type issues are handled (e.g., release dates, nulls, negative promo duration). See [preprocess.py](preprocess.py) and [popularity_score.py](popularity_score.py).
- Master merges produce a single feature‑rich dataset. See [dataset/Final_dataset](dataset/Final_dataset).

### 4) Feature engineering

- **Power scores**: Production houses and directors are scored based on historical day‑1 performance. See [popularity_score.py](popularity_score.py).
- **Time features**: Year, month, day of week, and promotion duration are derived from dates. See [popularity_score.py](popularity_score.py).
- **Genre encoding**: Top genres are converted to binary features. See [popularity_score.py](popularity_score.py) and [encoding.py](encoding.py).
- **Final feature selection**: Curated model‑ready columns are saved. See [final_coln_selection.py](final_coln_selection.py) and [model_train_features.py](model_train_features.py).

### 5) Modeling

- The target variable `Day1_collection_cr` is binned into classes:
  - Low (< 5 Cr)
  - Medium (5–20 Cr)
  - High (> 20 Cr)
- Models trained and compared:
  - Random Forest
  - XGBoost
  - LightGBM
- Artifacts and metrics are saved to [dataset/models](dataset/models) and [dataset/visuals](dataset/visuals).
- Training pipeline is in [model_training.py](model_training.py).

### 6) EDA and visualization

- Generates plots for top directors/production houses, genre distribution, and correlation heatmaps. See [EDA.py](EDA.py).

## Datasets (outputs)

Key outputs are stored in [dataset](dataset):

- Encoded features: [dataset/encoded.csv](dataset/encoded.csv)
- Merged + engineered features: [dataset/Final_dataset/movies_all_features_processed_v2.csv](dataset/Final_dataset/movies_all_features_processed_v2.csv)
- Final model‑ready training set: [dataset/Final_dataset/model_training_dataset_FINAL10.csv](dataset/Final_dataset/model_training_dataset_FINAL10.csv)
- Model artifacts and metrics: [dataset/models](dataset/models) and [dataset/visuals](dataset/visuals)

## How the pipeline fits together

1. **Scrape movie lists** → [scrape.py](scrape.py)
2. **Fetch metadata & box office** → [TMDB_Data_collection.py](TMDB_Data_collection.py), [scrape_boxoffice.py](scrape_boxoffice.py)
3. **Add YouTube trailer signals** → [dataset/hindi_sentiment.csv](dataset/hindi_sentiment.csv)
4. **Clean + engineer features** → [popularity_score.py](popularity_score.py), [preprocess.py](preprocess.py)
5. **Select final columns** → [final_coln_selection.py](final_coln_selection.py)
6. **Train and compare models** → [model_training.py](model_training.py)
