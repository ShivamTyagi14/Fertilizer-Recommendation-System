
# ==========================================
# SMART FERTILIZER RECOMMENDATION SYSTEM
# DATA CLEANING
# ==========================================

import pandas as pd
import os

print("DATA CLEANING STARTED")
print("==============================")


# STEP 1: Load original datasets

fertilizer_data = pd.read_csv(
    "data/raw/fertilizer_prediction.csv"
)

soil_data = pd.read_csv(
    "data/raw/agrinet_soil.csv"
)


# STEP 2: Check original dataset sizes

print("\nORIGINAL DATASET SIZES")

print("Fertilizer Dataset:", fertilizer_data.shape)
print("AgriNet Dataset:", soil_data.shape)


# STEP 3: Check missing values

print("\nMISSING VALUES IN FERTILIZER DATASET")

print(fertilizer_data.isnull().sum())

print("\nMISSING VALUES IN AGRINET DATASET")

print(soil_data.isnull().sum())


# STEP 4: Check duplicate records

print("\nDUPLICATE RECORDS")

print(
    "Fertilizer Dataset:",
    fertilizer_data.duplicated().sum()
)

print(
    "AgriNet Dataset:",
    soil_data.duplicated().sum()
)


# STEP 5: Remove exact duplicate records

fertilizer_cleaned = fertilizer_data.drop_duplicates()

soil_cleaned = soil_data.drop_duplicates()


# STEP 6: Handle missing values

# Remove rows having missing values
# We will review the missing-value report first.

fertilizer_cleaned = fertilizer_cleaned.dropna()

soil_cleaned = soil_cleaned.dropna()


# STEP 7: Check cleaned dataset sizes

print("\nCLEANED DATASET SIZES")

print("Fertilizer Dataset:", fertilizer_cleaned.shape)

print("AgriNet Dataset:", soil_cleaned.shape)


# STEP 8: Check remaining duplicates

print("\nREMAINING DUPLICATES")

print(
    "Fertilizer Dataset:",
    fertilizer_cleaned.duplicated().sum()
)

print(
    "AgriNet Dataset:",
    soil_cleaned.duplicated().sum()
)


# STEP 9: Create processed folder if necessary

os.makedirs("data/processed", exist_ok=True)


# STEP 10: Save cleaned datasets

fertilizer_cleaned.to_csv(
    "data/processed/fertilizer_cleaned.csv",
    index=False
)

soil_cleaned.to_csv(
    "data/processed/agrinet_cleaned.csv",
    index=False
)


print("\nCLEANED DATASETS SAVED SUCCESSFULLY!")

print("==============================")
print("DATA CLEANING COMPLETED")
