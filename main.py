
# ---------------------------------------
# SMART FERTILIZER RECOMMENDATION SYSTEM
# ---------------------------------------

# Step 1: Import Pandas
import pandas as pd

print("SMART FERTILIZER RECOMMENDATION SYSTEM")
print("---------------------------------------")


# Step 2: Load Fertilizer Prediction Dataset

fertilizer_data = pd.read_csv(
    "data/raw/fertilizer_prediction.csv"
)

print("\nFERTILIZER DATASET LOADED SUCCESSFULLY!")


# Step 3: Load AgriNet Soil Dataset

soil_data = pd.read_csv(
    "data/raw/agrinet_soil.csv"
)

print("AGRINET SOIL DATASET LOADED SUCCESSFULLY!")


# Step 4: Display first five records

print("\nFIRST FIVE RECORDS OF FERTILIZER DATASET:")
print(fertilizer_data.head())

print("\nFIRST FIVE RECORDS OF AGRINET DATASET:")
print(soil_data.head())


# Step 5: Display dataset dimensions

print("\nFERTILIZER DATASET SHAPE:")
print(fertilizer_data.shape)

print("\nAGRINET DATASET SHAPE:")
print(soil_data.shape)


# Step 6: Display column names

print("\nFERTILIZER DATASET COLUMNS:")
print(fertilizer_data.columns.tolist())

print("\nAGRINET DATASET COLUMNS:")
print(soil_data.columns.tolist())


# Step 7: Check missing values

print("\nMISSING VALUES IN FERTILIZER DATASET:")
print(fertilizer_data.isnull().sum())

print("\nMISSING VALUES IN AGRINET DATASET:")
print(soil_data.isnull().sum())


# Step 8: Check duplicate records

print("\nDUPLICATE RECORDS IN FERTILIZER DATASET:")
print(fertilizer_data.duplicated().sum())

print("\nDUPLICATE RECORDS IN AGRINET DATASET:")
print(soil_data.duplicated().sum())


print("\n---------------------------------------")
print("DATASET INSPECTION COMPLETED!")
