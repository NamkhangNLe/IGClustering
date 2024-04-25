import pandas as pd
import json

# Load the data from the JSON files
with open('Namkhang-Followers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
followers = pd.DataFrame(data['followers'])

with open('Namkhang-Following.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
following = pd.DataFrame(data['followings'])

# Merge the two DataFrames on the 'username' field
merged = pd.merge(followers, following, on='username')

# Remove the 'full_name_y' column
merged = merged.drop('full_name_y', axis=1)

# Rename 'full_name_x' to 'full_name'
merged = merged.rename(columns={'full_name_x': 'full_name'})

# Write the merged DataFrame to a CSV file
merged.to_csv('Merged.csv', index=False)