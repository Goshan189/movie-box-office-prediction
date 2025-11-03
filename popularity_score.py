import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import MinMaxScaler
import os
from datetime import datetime

# --- Configuration ---
INPUT_CSV = "dataset/Final_dataset/merged_dataset_1.csv"
OUTPUT_DIR = "dataset/Final_dataset"
# This is the single, final file that will be saved
OUTPUT_CSV = os.path.join(OUTPUT_DIR, 'movies_all_features_processed_v2.csv')
TOP_N_GENRES = 6


# ==============================================================================
# PHASE 1 FUNCTION
# ==============================================================================
def popularity_score(input_file):
    """
    Phase 1: Loads the data and creates data-driven 'power scores'
    for Production Companies and Directors based on Day 1 collections.
    Returns a DataFrame with these new columns added.
    """
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} movies from '{input_file}'.")

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        required_cols = ['Production Company', 'Day1_collection_cr', 'Director']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"Error: The input CSV is missing the following required columns: {missing_cols}")
            return None
        else:
            print("All required columns found. Starting Phase 1 processing...")
            df_processed = df.copy()

            # --- Production House Score ---
            print("\n--- Processing Production House Score (Top 15, 0-100) ---")
            df_processed['Production Company'] = df_processed['Production Company'].fillna('')
            all_companies = df_processed[df_processed['Production Company'] != '']['Production Company'].str.split(
                ',').explode().str.strip()
            top_15_companies = all_companies.value_counts().index[:15].tolist()

            company_scores = {}
            for company in top_15_companies:
                mask = df_processed['Production Company'].str.contains(re.escape(company), na=False)
                avg_score = df_processed[mask]['Day1_collection_cr'].mean()
                company_scores[company] = avg_score

            other_company_mask = ~df_processed['Production Company'].str.contains(
                '|'.join(re.escape(c) for c in top_15_companies), na=False)
            other_score = df_processed[other_company_mask]['Day1_collection_cr'].mean()

            def map_company_score(row_companies_str):
                for company, score in company_scores.items():
                    if company in row_companies_str:
                        return score
                return other_score

            df_processed['Production_House_Score_Raw'] = df_processed['Production Company'].apply(map_company_score)
            scaler_prod = MinMaxScaler(feature_range=(0, 100))
            df_processed['Production_House_Score'] = scaler_prod.fit_transform(
                df_processed[['Production_House_Score_Raw']])
            print("Created and normalized 'Production_House_Score'.")

            # --- Director Score ---
            print("\n--- Processing Director Score (Top 15, 0-100) ---")
            df_processed['Director'] = df_processed['Director'].fillna('')
            all_directors = df_processed[df_processed['Director'] != '']['Director'].str.split(
                ',').explode().str.strip()
            top_15_directors = all_directors.value_counts().index[:15].tolist()

            director_scores = {}
            for director in top_15_directors:
                mask = df_processed['Director'].str.contains(re.escape(director), na=False)
                avg_score = df_processed[mask]['Day1_collection_cr'].mean()
                director_scores[director] = avg_score

            other_director_mask = ~df_processed['Director'].str.contains(
                '|'.join(re.escape(d) for d in top_15_directors), na=False)
            other_director_score = df_processed[other_director_mask]['Day1_collection_cr'].mean()

            def map_director_score(row_director_str):
                for director, score in director_scores.items():
                    if director in row_director_str:
                        return score
                return other_director_score

            df_processed['Director_Score_Raw'] = df_processed['Director'].apply(map_director_score)
            scaler_dir = MinMaxScaler(feature_range=(0, 100))
            df_processed['Director_Score'] = scaler_dir.fit_transform(df_processed[['Director_Score_Raw']])
            print("Created and normalized 'Director_Score'.")

            print("\n✅ Phase 1 Complete.")
            return df_processed

    except FileNotFoundError:
        print(f"Error: The input file '{INPUT_CSV}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in Phase 1: {e}")
        return None


# ==============================================================================
# PHASE 2 FUNCTION
# ==============================================================================
def simplify_genre(df_from_phase1):
    """
    Phase 2: Takes the DataFrame from Phase 1, creates dummy columns
    from the 'Genre' text column, and adds the Top 6 + Other genres.
    """
    try:
        df = df_from_phase1.copy()
        print(f"\nReceived {len(df)} rows from Phase 1. Starting Phase 2 (Genres)...")

        print(f"--- Processing Top {TOP_N_GENRES} Genres ---")

        if 'Genre' not in df.columns:
            print("Error: A 'Genre' text column was not found in the DataFrame.")
            return None

        df['Genre'] = df['Genre'].fillna('').str.strip()
        genre_dummies = df['Genre'].str.get_dummies(sep=',')
        genre_dummies.columns = genre_dummies.columns.str.strip()

        # Fix for duplicate column names (e.g., 'Drama' and ' Drama')
        genre_dummies = genre_dummies.groupby(level=0, axis=1).sum().clip(upper=1)

        if genre_dummies.empty:
            print("Error: No genres were found to encode.")
            return None

        genre_counts = genre_dummies.sum().sort_values(ascending=False)
        top_6_genres = genre_counts.index[:TOP_N_GENRES].tolist()
        other_genres = genre_counts.index[TOP_N_GENRES:].tolist()

        print(f"Top {TOP_N_GENRES} Genres found: {top_6_genres}")

        for col_name in top_6_genres:
            df[f'Genre_{col_name}'] = genre_dummies[col_name]
        df['Genre_Other'] = genre_dummies[other_genres].sum(axis=1).clip(upper=1)

        print("\n✅ Phase 2 Complete.")
        return df  # Return the modified DataFrame

    except Exception as e:
        print(f"An unexpected error occurred in Phase 2: {e}")
        return None


# ==============================================================================
# PHASE 3 FUNCTION
# ==============================================================================
def process_time_features(df_from_phase2):
    """
    Phase 3: Processes date columns to extract predictive features.
    - Splits 'Release Date' into Year, Month, and Day_of_Week.
    - Creates 'Promotion_Duration_Days' from 'published_at' and 'Release Date'.
    """
    try:
        df = df_from_phase2.copy()
        print(f"\nReceived {len(df)} rows from Phase 2. Starting Phase 3 (Time Features)...")

        # --- Process 'Release Date' ---
        if 'Release Date' not in df.columns:
            print("  -> Warning: 'Release Date' column not found. Skipping.")
        else:
            df['Release Date'] = pd.to_datetime(df['Release Date'], format='%d-%m-%Y', errors='coerce')
            df['Release_Year'] = df['Release Date'].dt.year
            df['Release_Month'] = df['Release Date'].dt.month
            df['Release_Day_of_Week'] = df['Release Date'].dt.dayofweek  # Monday=0, Sunday=6
            print("  -> Created 'Release_Year', 'Release_Month', 'Release_Day_of_Week'")

        # --- Process 'published_at' ---
        if 'published_at' not in df.columns or 'Release Date' not in df.columns:
            print("  -> Warning: 'published_at' or 'Release Date' not found. Skipping 'Promotion_Duration_Days'.")
        else:
            df['published_at'] = pd.to_datetime(df['published_at'], format='%Y-%m-%d', errors='coerce')
            time_delta = df['Release Date'] - df['published_at']
            df['Promotion_Duration_Days'] = time_delta.dt.days
            print("  -> Created 'Promotion_Duration_Days'")

        # Drop the original date columns
        df = df.drop(columns=['Release Date', 'published_at'], errors='ignore')

        print("\n✅ Phase 3 Complete.")
        return df

    except Exception as e:
        print(f"An unexpected error occurred in Phase 3: {e}")
        return None


# ==============================================================================
# PHASE 4 FUNCTION (New)
# ==============================================================================
def fix_promotion_days(df_from_phase3):
    """
    Phase 4: Cleans the 'Promotion_Duration_Days' column.
    - Replaces all negative values with 0.
    - Fills all empty (NaN) values with 0.
    """
    try:
        df = df_from_phase3.copy()
        print(f"\nReceived {len(df)} rows from Phase 3. Starting Phase 4 (Fixing Promotion Days)...")

        if 'Promotion_Duration_Days' in df.columns:
            # Check how many values are negative before fixing
            negative_values = df[df['Promotion_Duration_Days'] < 0].shape[0]
            nan_values = df['Promotion_Duration_Days'].isnull().sum()

            print(f"  -> Found {negative_values} movies with negative promotion days.")
            print(f"  -> Found {nan_values} movies with empty (NaN) promotion days.")

            # --- THIS IS THE FIX ---
            # .clip(lower=0) sets any value below 0 to 0.
            # .fillna(0) will set any NaN values to 0 as well.
            df['Promotion_Duration_Days'] = df['Promotion_Duration_Days'].clip(lower=0).fillna(0)

            print("  -> All negative and empty values have been set to 0.")
        else:
            print("  -> 'Promotion_Duration_Days' column not found.")

        print("\n✅ Phase 4 Complete.")
        return df

    except Exception as e:
        print(f"An unexpected error occurred in Phase 4: {e}")
        return None


# ==============================================================================
# --- Main Execution Pipeline ---
# ==============================================================================
if __name__ == "__main__":

    # Run Phase 1
    df_after_phase1 = popularity_score(INPUT_CSV)

    # Run Phase 2
    if df_after_phase1 is not None:
        df_after_phase2 = simplify_genre(df_after_phase1)
    else:
        df_after_phase2 = None
        print("\nAborting pipeline due to Phase 1 failure.")

    # Run Phase 3
    if df_after_phase2 is not None:
        df_after_phase3 = process_time_features(df_after_phase2)
    else:
        df_after_phase3 = None
        print("\nAborting pipeline due to Phase 2 failure.")

    # Run Phase 4 (New Step)
    if df_after_phase3 is not None:
        df_after_phase4 = fix_promotion_days(df_after_phase3)
    else:
        df_after_phase4 = None
        print("\nAborting pipeline due to Phase 3 failure.")

    # Final Save
    if df_after_phase4 is not None:
        df_after_phase4.to_csv(OUTPUT_CSV, index=False)
        print(f"\n\n✅✅✅ Feature Engineering Pipeline Complete! ✅✅✅")
        print(f"Final processed file saved to: {OUTPUT_CSV}")
    else:
        print("\n\nPipeline failed. No file was saved.")