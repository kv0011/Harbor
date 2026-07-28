"""
Trains the Random Forest phishing-detection model from the labeled CSVs
and saves it to RandomForestModel.sav for app.py to load.

Run this once (from this folder) whenever you want to retrain:
    python Classifier.py
"""

import pandas as pd
import random
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report

from FeatureExtraction import MODEL_FEATURE_COLUMNS

# ## Collection of Data
legitimate_urls = pd.read_csv("legitimate-urls.csv")
phishing_urls = pd.read_csv("phishing-urls.csv")

print(f"legitimate examples: {len(legitimate_urls)}")
print(f"phishing examples:   {len(phishing_urls)}")

# ## Data PreProcessing
# The two CSVs share the same columns, so stack them into one dataframe.
# (pandas removed DataFrame.append() in 2.0; pd.concat is the replacement.)
urls = pd.concat([legitimate_urls, phishing_urls], ignore_index=True)
print(f"total examples: {len(urls)}")
print(f"columns: {list(urls.columns)}")

# #### Selecting only the model's feature columns (by name, not position)
# This must exactly match MODEL_FEATURE_COLUMNS in FeatureExtraction.py --
# that's the shared source of truth so training and inference never drift
# apart. (The previous version of this script dropped columns by numeric
# position, which silently picked the wrong columns and left string
# Domain/Path columns in the training data.)
labels = urls['label']
urls_without_labels = urls[MODEL_FEATURE_COLUMNS]

# Since we stacked two dataframes, the first half of rows is all
# legitimate and the second half is all phishing. If we split into
# train/test now without shuffling, the split would be wildly imbalanced,
# so shuffle rows first.
random.seed(100)
shuffled = urls.sample(frac=1, random_state=100).reset_index(drop=True)
shuffled_labels = shuffled['label']
shuffled_features = shuffled[MODEL_FEATURE_COLUMNS]

# #### Splitting into train/test sets
data_train, data_test, labels_train, labels_test = train_test_split(
    shuffled_features, shuffled_labels, test_size=0.20, random_state=100
)
print(f"train size: {len(data_train)}, test size: {len(data_test)}")
print("train label distribution:")
print(labels_train.value_counts())
print("test label distribution:")
print(labels_test.value_counts())

# ## Random Forest
RFmodel = RandomForestClassifier(n_estimators=100, random_state=100)
RFmodel.fit(data_train, labels_train)
rf_pred_label = RFmodel.predict(data_test)

cm2 = confusion_matrix(labels_test, rf_pred_label)
print("confusion matrix:")
print(cm2)
print(f"accuracy: {accuracy_score(labels_test, rf_pred_label):.4f}")
print(classification_report(labels_test, rf_pred_label, target_names=["legitimate", "phishing"]))

# Saving the trained model to a file for app.py to load.
file_name = "RandomForestModel.sav"
pickle.dump(RFmodel, open(file_name, 'wb'))
print(f"saved trained model to {file_name}")
