
import pandas as pd
import os

print("SOIL NUTRIENT ANALYSIS")
print("====================================")

# STEP 1: LOAD THE CLEANED SOIL DATASET

soil_data = pd.read_csv(
    "data/processed/agrinet_cleaned.csv"
)

print("\nDataset loaded successfully!")

print("Total soil samples:", soil_data.shape[0])
print("Total columns:", soil_data.shape[1])

# STEP 2: DISPLAY ALL COLUMN NAMES

print("\nSOIL DATASET PARAMETERS")
print("------------------------------------")

for column in soil_data.columns:
    print("-", column)

# STEP 3: CHECK DATA TYPES

print("\nDATA TYPES")
print("------------------------------------")
print(soil_data.dtypes)

# STEP 4: GENERATE STATISTICAL SUMMARY

print("\nSOIL NUTRIENT STATISTICS")
print("------------------------------------")

numeric_data = soil_data.select_dtypes(
    include="number"
)

summary = numeric_data.describe().T

print(summary.round(2))

# STEP 5: CHECK MISSING VALUES

print("\nMISSING VALUES")
print("------------------------------------")
print(soil_data.isnull().sum())

# STEP 6: DISPLAY SAMPLE RECORDS

print("\nFIRST FIVE SOIL SAMPLES")
print("------------------------------------")
print(soil_data.head().to_string(index=False))

# STEP 7: SAVE THE ANALYSIS REPORT

os.makedirs("outputs/soil_analysis", exist_ok=True)

summary.to_csv(
    "outputs/soil_analysis/soil_statistics.csv"
)

soil_data.head(10).to_csv(
    "outputs/soil_analysis/soil_sample_records.csv",
    index=False
)

print("\n====================================")
print("SOIL ANALYSIS REPORT GENERATED!")
print("Saved in outputs/soil_analysis/")
print("====================================")
