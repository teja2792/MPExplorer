import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
from feature_engineering import build_feature_matrix

df = pd.read_csv("data/mp_summary.csv")
X_scaled, feature_names, metadata_df = build_feature_matrix(df)

print(f"Feature matrix shape: {X_scaled.shape}")
print(f"Feature names: {list(feature_names)}")
print()
print(metadata_df.head(10))