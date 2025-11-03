import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration ---
# THIS MUST BE THE FINAL, FULLY PROCESSED FILE
INPUT_CSV = "dataset/Final_dataset/movies_all_features_processed_v2.csv"
OUTPUT_DIR = "dataset/visuals/"
TOP_N = 15
TOP_N_GENRES_FOR_PIE = 6

try:
    # Load the dataset
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from '{INPUT_CSV}' for visualization.")

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Set a consistent, professional style for all plots
    sns.set_style("whitegrid")

    # ==============================================================================
    # 1. Bar Chart for Top 15 Directors (Based on Text Column Counts)
    # ==============================================================================
    print("Generating bar chart for Top 15 Directors...")

    if 'Director' in df.columns:
        director_counts = df['Director'].fillna('').str.split(',').explode().str.strip()
        director_counts = director_counts[director_counts != '']
        top_15_directors = director_counts.value_counts().head(TOP_N)

        plt.figure(figsize=(12, 8))
        sns.barplot(x=top_15_directors.values, y=top_15_directors.index, palette='viridis')
        plt.title('Movie Counts for Top 15 Directors', fontsize=16)
        plt.xlabel('Number of Movies', fontsize=12)
        plt.ylabel('Director', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'director_top15_barplot.png'))
        plt.close()
        print("  -> Saved 'director_top15_barplot.png'")
    else:
        print("  -> Warning: 'Director' text column not found.")

    # ==============================================================================
    # 2. Bar Chart for Top 15 Production Companies (Based on Text Column Counts)
    # ==============================================================================
    print("Generating bar chart for Top 15 Production Companies...")

    if 'Production Company' in df.columns:
        company_counts = df['Production Company'].fillna('').str.split(',').explode().str.strip()
        company_counts = company_counts[company_counts != '']
        top_15_companies = company_counts.value_counts().head(TOP_N)

        plt.figure(figsize=(12, 8))
        sns.barplot(x=top_15_companies.values, y=top_15_companies.index, palette='plasma')
        plt.title('Movie Counts for Top 15 Production Companies', fontsize=16)
        plt.xlabel('Number of Movies', fontsize=12)
        plt.ylabel('Production Company', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'production_top15_barplot.png'))
        plt.close()
        print("  -> Saved 'production_top15_barplot.png'")
    else:
        print("  -> Warning: 'Production Company' text column not found.")

    # ==============================================================================
    # 3. Pie Chart for Top 6 Genres + Other (Full Pie Chart)
    # ==============================================================================
    print("Generating pie chart for Top 6 Genres + Other...")

    genre_cols = [col for col in df.columns if col.startswith('Genre_')]

    if genre_cols:
        primary_genre_cols = [col for col in genre_cols if col != 'Genre_Other']
        top_6_counts = df[primary_genre_cols].sum().sort_values(ascending=False).head(TOP_N_GENRES_FOR_PIE)

        other_count = df['Genre_Other'].sum()

        pie_data = top_6_counts.copy()
        pie_data['Other'] = other_count

        labels = [f'{name.replace("Genre_", "")}\n(n={int(count)})' for name, count in pie_data.items()]

        plt.figure(figsize=(10, 10))
        plt.pie(pie_data, labels=labels, autopct='%1.1f%%', startangle=90,
                wedgeprops={'edgecolor': 'white'}, pctdistance=0.85)

        plt.title(f'Genre Distribution (Top {TOP_N_GENRES_FOR_PIE} + Other)', fontsize=16)
        plt.axis('equal')  # Ensures the pie chart is a circle
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'genre_top6_piechart.png'))
        plt.close()
        print("  -> Saved 'genre_top6_piechart.png'")
    else:
        print("  -> Warning: No 'Genre_' columns found.")

    # ==============================================================================
    # 4. NEW: Correlation Matrix Heatmap
    # ==============================================================================
    print("Generating correlation matrix heatmap...")

    # Define the list of all final, model-ready numeric/binary columns
    model_features = [
        'Day1_collection_cr',
        'Runtime (min)',
        'Production_House_Score',
        'Director_Score',
        'Release_Year',
        'Release_Month',
        'Release_Day_of_Week',
        'Promotion_Duration_Days',
        'avg_sentiment',  # Assuming you have this
        'median_sentiment'  # Assuming you have this
    ]

    # Add all the genre columns to our list
    model_features.extend(genre_cols)

    # Filter the DataFrame to only these columns
    df_model = df[model_features].copy()

    # Drop rows where our target is empty
    df_model.dropna(subset=['Day1_collection_cr'], inplace=True)

    # Calculate the correlation matrix
    corr_matrix = df_model.corr()

    # --- Plot 1: Full Heatmap (Good for seeing feature-feature correlation) ---
    plt.figure(figsize=(20, 16))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                annot_kws={"size": 8})
    plt.title('Correlation Matrix of All Model Features', fontsize=18)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'correlation_heatmap_full.png'))
    plt.close()
    print("  -> Saved 'correlation_heatmap_full.png'")

    # --- Plot 2: Target Correlation Bar Chart (Easier to read) ---
    # Get only the correlations with the target variable
    corr_target = corr_matrix['Day1_collection_cr'].drop('Day1_collection_cr').sort_values(ascending=False)

    plt.figure(figsize=(12, 10))
    sns.barplot(x=corr_target.values, y=corr_target.index, palette='vlag')
    plt.title('Feature Correlation with Day 1 Collection', fontsize=16)
    plt.xlabel('Correlation Coefficient', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'correlation_with_target.png'))
    plt.close()
    print("  -> Saved 'correlation_with_target.png'")

    print("\n✅ Visualization script complete.")

except FileNotFoundError:
    print(f"\nError: The input file '{INPUT_CSV}' was not found.")
    print(f"Please make sure the file '{INPUT_CSV}' exists.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")