import pandas as pd
import os

# --- Configuration ---
# This is the "master" file with all columns
INPUT_CSV = "dataset/Final_dataset/movies_all_features_processed_v2.csv"
OUTPUT_DIR = "dataset/Final_dataset"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, 'model_training_dataset.csv')

# ==============================================================================
# FINAL FEATURE SELECTION
# ==============================================================================

# Define the exact list of all columns we want to keep for the model.
FINAL_COLUMNS_FOR_MODEL = [

    # --- 1. The Target Variable (y) ---
    'Day1_collection_cr',

    # --- 2. The Features (X) ---

    # Power Scores
    'Production_House_Score',
    'Director_Score',

    # Time-Based Features
    'Runtime (min)',
    'Release_Year',
    'Release_Month',
    'Release_Day_of_Week',
    'Promotion_Duration_Days',

    # Genre Features
    'Genre_Drama',
    'Genre_Comedy',
    'Genre_Action',
    'Genre_Thriller',
    'Genre_Romance',
    'Genre_Crime',
    'Genre_Other',

    # Sentiment Features
    'avg_sentiment',
    'median_sentiment',

    # Raw Trailer Stats (Optional, but good to include)
    'viewCount',
    'likeCount',
    'commentCount'
]

try:
    # Load the "master" file
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from '{INPUT_CSV}'.")

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Check if all desired columns are in the DataFrame
    missing_cols = [col for col in FINAL_COLUMNS_FOR_MODEL if col not in df.columns]

    if missing_cols:
        print(f"\nError: The DataFrame is missing the following expected columns: {missing_cols}")
        print("Please check the column names in your file and the script.")
    else:
        # Create the final DataFrame with only these columns
        df_model_ready = df[FINAL_COLUMNS_FOR_MODEL]

        print(f"\nSuccessfully selected {len(df_model_ready.columns)} columns for the model.")

        # --- Handle Missing Values ---
        # Before training, a model needs all NaNs to be filled.
        # We will fill them with 0 here.
        df_model_ready.fillna(0, inplace=True)
        print("Filled all remaining empty (NaN) values with 0.")

        # Save the final model-ready file
        df_model_ready.to_csv(OUTPUT_CSV, index=False)

        print(f"\n✅✅✅ All Processing Complete! ✅✅✅")
        print(f"Your final, model-ready dataset is saved to:\n{OUTPUT_CSV}")

except FileNotFoundError:
    print(f"Error: The input file '{INPUT_CSV}' was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")