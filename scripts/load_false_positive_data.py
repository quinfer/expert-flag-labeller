#!/usr/bin/env python3
import pickle
import pandas as pd
import json

# Load false positive data
print("Loading false positive data...")
df = pd.read_pickle('false_positive_checks/ENNISKILLENresultsCORRECT.pickle')

# Load expert confirmed list
print("Loading expert confirmed list...")
expert_confirmed_data = pickle.load(open('flag_imagesCORRECT/ENNISKILLENflag_imagesCORRECTlist.pickle', 'rb'))
expert_confirmed = set([row[0] for row in expert_confirmed_data])

# Create comprehensive dataset
result = {
    'false_positive_data': df.fillna('NaN').to_dict('records'),
    'expert_confirmed': list(expert_confirmed),
    'metadata': {
        'total_records': len(df),
        'expert_confirmed_count': len(expert_confirmed),
        'columns': list(df.columns)
    }
}

# Write to file
output_file = 'scripts/false_positive_data.json'
print(f"Writing data to {output_file}...")
with open(output_file, 'w') as f:
    json.dump(result, f)

print(f"✅ Data saved to {output_file}")
print(f"📊 Total records: {len(df)}")
print(f"🏆 Expert confirmed: {len(expert_confirmed)}") 