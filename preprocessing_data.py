
import pandas as pd
import numpy as np
import os
import joblib

from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

print("MACHINE LEARNING DATA PREPROCESSING")
print("====================================")


# STEP 1: Load training and testing datasets

X_train = pd.read_csv("data/processed/splits/X_train.csv")
X_test = pd.read_csv("data/processed/splits/X_test.csv")

y_train = pd.read_csv("data/processed/splits/y_train.csv")
y_test = pd.read_csv("data/processed/splits/y_test.csv")

print("\nDatasets Loaded Successfully!")

print("Training Data:", X_train.shape)
print("Testing Data:", X_test.shape)


# STEP 2: Identify numerical and categorical columns

numerical_features = [
    "Temparature",
    "Humidity",
    "Moisture",
    "Nitrogen",
    "Potassium",
    "Phosphorous"
]

categorical_features = [
    "Soil_Type",
    "Crop_Type"
]


# STEP 3: Create preprocessing system

preprocessor = ColumnTransformer(
    transformers=[
        ("numerical", StandardScaler(), numerical_features),
        ("categorical", OneHotEncoder(handle_unknown="ignore"),
         categorical_features)
    ]
)


# STEP 4: Fit on training data and transform it

X_train_encoded = preprocessor.fit_transform(X_train)


# STEP 5: Transform testing data using the same preprocessor

X_test_encoded = preprocessor.transform(X_test)


# STEP 6: Convert transformed data into arrays

if hasattr(X_train_encoded, "toarray"):
    X_train_encoded = X_train_encoded.toarray()

if hasattr(X_test_encoded, "toarray"):
    X_test_encoded = X_test_encoded.toarray()


# STEP 7: Get the names of the new columns

feature_names = preprocessor.get_feature_names_out()

X_train_final = pd.DataFrame(
    X_train_encoded,
    columns=feature_names
)

X_test_final = pd.DataFrame(
    X_test_encoded,
    columns=feature_names
)


# STEP 8: Create output folder

os.makedirs("data/processed/preprocessed", exist_ok=True)
os.makedirs("models", exist_ok=True)


# STEP 9: Save preprocessed datasets

X_train_final.to_csv(
    "data/processed/preprocessed/X_train_encoded.csv",
    index=False
)

X_test_final.to_csv(
    "data/processed/preprocessed/X_test_encoded.csv",
    index=False
)

y_train.to_csv(
    "data/processed/preprocessed/y_train.csv",
    index=False
)

y_test.to_csv(
    "data/processed/preprocessed/y_test.csv",
    index=False
)


# STEP 10: Save preprocessing object

joblib.dump(
    preprocessor,
    "models/preprocessor.pkl"
)


# STEP 11: Display results

print("\nPREPROCESSING COMPLETED!")

print("\nOriginal Training Shape:", X_train.shape)
print("Encoded Training Shape:", X_train_final.shape)

print("\nOriginal Testing Shape:", X_test.shape)
print("Encoded Testing Shape:", X_test_final.shape)

print("\nNew Feature Names:")
print(list(feature_names))

print("\nPreprocessed datasets saved successfully!")
print("Preprocessor saved in models/preprocessor.pkl")

print("\n====================================")
print("STEP 9 COMPLETED SUCCESSFULLY!")
    