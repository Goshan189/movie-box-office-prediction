import pandas as pd
import re
# --- Configuration ---
# TODO: Change this to the name of your input file
INPUT_CSV = 'dataset/hindi_movies_features_Completed2.csv'
OUTPUT_CSV = 'dataset/encoded.csv'

try:
    # --- Load the Dataset ---
    df = pd.read_csv(INPUT_CSV,encoding='latin1')
    print(f"Loaded {len(df)} rows from '{INPUT_CSV}'.")


    print("\n--- Part 1: Processing Release Date ---")

    # Convert the 'Release Date' column to a proper datetime format
    # errors='coerce' will turn any un-parseable dates into NaT (Not a Time)
    df['Release Date'] = pd.to_datetime(df['Release Date'], format='%d-%m-%Y', errors='coerce')

    # Create new columns for Day, Month, and Year
    df['Release_Year'] = df['Release Date'].dt.year
    df['Release_Month'] = df['Release Date'].dt.month
    df['Release_Day'] = df['Release Date'].dt.day

    # Drop the original 'Release Date' column as it's no longer needed
    df.drop(columns=['Release Date'], inplace=True)
    print("Split 'Release Date' into 'Release_Year', 'Release_Month', 'Release_Day'.")

    print("\n--- Part 2: Encoding Categorical Features ---")


    print("Encoding 'Genre' column...")
    # Clean up whitespace and then create dummy columns
    df['Genre'] = df['Genre'].str.strip()
    genre_dummies = df['Genre'].str.get_dummies(sep=', ')
    # Add a prefix to avoid name collisions
    genre_dummies = genre_dummies.add_prefix('Genre_')
    df = pd.concat([df, genre_dummies], axis=1)


    for column_name, top_n in [('Director', 15), ('Production Company', 15)]:
        print(f"Encoding Top {top_n} from '{column_name}' column...")

        # Handle missing values before processing
        df[column_name] = df[column_name].fillna('')

        # Find the most frequent items
        # .split(',') -> .explode() creates a new row for each item
        # .str.strip() cleans whitespace
        # .value_counts() counts them
        top_items = df[column_name].str.split(',').explode().str.strip().value_counts().index[:top_n]

        print(f"  - Top {top_n} items found: {list(top_items)}")

        # Create a new binary column for each of the top items
        for item in top_items:
            new_col_name = f"{column_name}_{item}".replace(' ', '_')  # Create a clean column name
            df[new_col_name] = df[column_name].str.contains(re.escape(item), na=False).astype(int)

    # Drop the original text columns after encoding
    df.drop(columns=['Genre', 'Director', 'Production Company'], inplace=True)
    print("\nDropped original text columns: 'Genre', 'Director', 'Production Company'.")

    # --- Final Save ---
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Success! Processed data saved to '{OUTPUT_CSV}'.")
    print("The file is now ready for machine learning.")

except FileNotFoundError:
    print(f"Error: The input file '{INPUT_CSV}' was not found.")