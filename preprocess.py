import pandas as pd

INPUT_DATA='dataset/Final_dataset/model_training_dataset_FINAL10.csv'

data=pd.read_csv(INPUT_DATA,encoding="latin1")

print(data.shape)
print(data.columns)
print(data.isnull().sum())
#print(data.isnull().sum())

CHECK_COL=[
    'Day1_collection_cr',
    'Banner',
    'Release Date',
    'Genre',
    'Director',
    'Runtime (min)'
]


def missing(tamil_movies):
    for i in range(2016,2026):
            empty=data[data["Year"]==i]
            print(f"\n{i}\n{empty.isnull().sum()}")

def check_movie(data):
    check=['Nadaaniyan','The Diplomat','Sikandar ','Jaat','Chhorii 2','Kesari Chapter 2','Jewel Thief ','Bhool Chuk Maaf']
    for i in range(len(check)):
        title_check=data["Title"]==check[i].strip()
        if title_check.any():
            print(f"{check[i]} exist")
        else:
            print(f"{check[i]} not exist ")


def check_duplicate(data):
    duplicates_rows = data[data.duplicated()]
    print(len(duplicates_rows))
    data = data.drop_duplicates(subset='Title', keep=False)
    duplicates_rows = data[data.duplicated()]
    print(f" After dup removed:{len(duplicates_rows)}")


    data.to_csv('dataset/tamil_movies_3.csv', index=False)

def Movies_with_missing_vals(df):
    try:
        for column in CHECK_COL:
            if column in df.columns:
                missing_df = df[df[column].isnull()]
                titles_with_missing_data = missing_df['Title'].tolist()

                print(f"\n## Column: '{column}'")
                print(f"Found {len(titles_with_missing_data)} movies with missing data.")

                if titles_with_missing_data:
                    print("Movie Titles:")
                    for title in titles_with_missing_data:
                        print(f"  - {title}")
            else:
                print(f"\n## Column: '{column}'")
                print(f"  - Warning: This column was not found in the file.")

    except FileNotFoundError:
        print(f"\nError: The input file '{INPUT_DATA}' was not found.")
    except Exception as e:
        print(f"Error:{e}")

def Remove_Rows(data):
    print(data.isnull().sum())
    print(data.columns)
    data = data[~data["Day1_collection_cr"].isin(["NA", "NAT"])].dropna(subset=["Day1_collection_cr"])
    print(data.isnull().sum())
    data.to_csv("dataset/Final_dataset/hindi_movies_5.csv",index=False)
    print("over")

def merge_datasets():
    data1 = pd.read_csv("dataset/Final_dataset/hindi_movies_5.csv", encoding='latin1')
    data2 = pd.read_csv("dataset/Final_dataset/movie_trailers_youtube_stats.csv", encoding='latin1')
    merged_df=pd.merge(data1,data2,on="Title",how="inner")
    merged_df.to_csv("merged_dataset.csv", index=False)

def format_date(data):
    data["published_at"]=pd.to_datetime(data["published_at"],errors="coerce").dt.strftime("%Y-%m-%d")
    data.to_csv("dataset/Final_dataset/merged_dataset_1.csv",index=False)


#missing(data)
#check_movie(data)
#check_duplicate(data)
#Movies_with_missing_vals(data)
#null_titles_list = data[data['Day1_collection_cr'].isnull()]['Title'].tolist()
#print(null_titles_list)
#Remove_Rows(data)
#merge_datasets()
#format_date(data)

