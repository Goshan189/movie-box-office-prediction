import pandas as pd
import os
from sklearn.impute import KNNImputer

# --- Configuration ---
# This is the "master" file with all columns
INPUT_CSV = "dataset/Final_dataset/model_training_dataset_FINAL_WITH_CAST.csv"
OUTPUT_DIR = "dataset/Final_dataset"
# This is the final, 100% clean file for model training
OUTPUT_CSV = os.path.join(OUTPUT_DIR, 'model_training_dataset_FINAL10.csv')

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
    'Actor_Score',


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

    # Sentiment Features (with 170 NaNs)
    'avg_sentiment',
    'median_sentiment',

    # Raw Trailer Stats
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

    # --- Step 1: Select only the columns we will use for the model ---

    # Check if all desired columns are in the DataFrame
    missing_cols = [col for col in FINAL_COLUMNS_FOR_MODEL if col not in df.columns]

    if missing_cols:
        print(f"\nError: The DataFrame is missing the following expected columns: {missing_cols}")
    else:
        df_model = df[FINAL_COLUMNS_FOR_MODEL].copy()
        print(f"\nSuccessfully selected {len(df_model.columns)} columns for the model.")

        # ==============================================================================
        # NEW STEP: SYNTHETIC DATA IMPUTATION
        # ==============================================================================

        print("\nStarting synthetic data imputation for sentiment features...")

        # --- Step 2: Fill NaNs in non-sentiment columns with 0 ---
        # The imputer needs clean data to work with.
        # We fill all columns with 0 EXCEPT the ones we want to predict.
        cols_to_fill_zero = [
            'Runtime (min)', 'Release_Year', 'Release_Month', 'Release_Day_of_Week',
            'Promotion_Duration_Days', 'viewCount', 'likeCount', 'commentCount'
        ]

        for col in cols_to_fill_zero:
            df_model[col].fillna(0, inplace=True)

        print("  -> Pre-filled '0' for non-sentiment missing values.")

        # --- Step 3: Run the k-NN Imputer ---
        # This will predict the 170 missing values for 'avg_sentiment'
        # and 'median_sentiment' based on all the other columns.

        # We use n_neighbors=5 (a common default)
        imputer = KNNImputer(n_neighbors=5)

        # The imputer returns a numpy array, so we must re-create the DataFrame
        df_imputed_array = imputer.fit_transform(df_model)

        df_final = pd.DataFrame(df_imputed_array, columns=FINAL_COLUMNS_FOR_MODEL)

        print(f"  -> Successfully imputed {df_model['avg_sentiment'].isnull().sum()} missing sentiment values.")

        # ==============================================================================
        # FINAL SAVE
        # ==============================================================================

        # Save the final model-ready file
        df_final.to_csv(OUTPUT_CSV, index=False)

        print(f"\n✅✅✅ All Processing Complete! ✅✅✅")
        print(f"Your final, 100% clean, model-ready dataset is saved to:\n{OUTPUT_CSV}")

except FileNotFoundError:
    print(f"\nError: The input file '{INPUT_CSV}' was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")