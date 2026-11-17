
import pandas as pd
import os

from sklearn.model_selection import train_test_split

print("FEATURE SELECTION AND DATA PREPARATION")
print("========================================")

# STEP 1: Load cleaned fertilizer dataset

data = pd.read_csv(
    "data/processed/fertilizer_cleaned.csv"
)

print("\nDataset Loaded Successfully!")
print("Dataset Shape:", data.shape)


# STEP 2: Select input features (X)

features = [
    "Temparature",
    "Humidity",
    "Moisture",
    "Soil_Type",
    "Crop_Type",
    "Nitrogen",
    "Potassium",
    "Phosphorous"
]

X = data[features]


# STEP 3: Select target variable (y)

y = data["Fertilizer"]


# STEP 3A: Handle fertilizer class with only one record

rare_class = "Potassium chloride"

print("\nRemoving insufficiently represented class:")
print(rare_class)

# Remove the class from both X and y
valid_records = y != rare_class

X = X.loc[valid_records].copy()
y = y.loc[valid_records].copy()

print("\nUpdated Dataset Shape:", X.shape)
print("Updated Number of Fertilizer Classes:", y.nunique())



print("\nINPUT FEATURES:")
print(X.head())

print("\nTARGET VARIABLE:")
print(y.head())


# STEP 4: Check fertilizer class distribution

print("\nFERTILIZER CLASS DISTRIBUTION:")
print(y.value_counts())

print("\nNUMBER OF FERTILIZER CLASSES:")
print(y.nunique())


# STEP 5: Check whether stratified splitting is possible

class_counts = y.value_counts()

if class_counts.min() < 2:
    print("\nERROR: Some fertilizer classes have fewer than 2 records.")
    print("We need to inspect the rare classes before splitting.")
    print(class_counts[class_counts < 2])
    raise SystemExit


# STEP 6: Split dataset into training and testing data

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# STEP 7: Display training and testing sizes

print("\nTRAINING DATA SHAPE:")
print(X_train.shape)

print("\nTESTING DATA SHAPE:")
print(X_test.shape)

print("\nTRAINING TARGET SHAPE:")
print(y_train.shape)

print("\nTESTING TARGET SHAPE:")
print(y_test.shape)


# STEP 8: Save the prepared datasets

os.makedirs("data/processed/splits", exist_ok=True)

X_train.to_csv(
    "data/processed/splits/X_train.csv",
    index=False
)

X_test.to_csv(
    "data/processed/splits/X_test.csv",
    index=False
)

y_train.to_frame().to_csv(
    "data/processed/splits/y_train.csv",
    index=False
)

y_test.to_frame().to_csv(
    "data/processed/splits/y_test.csv",
    index=False
)


print("\n========================================")
print("DATA PREPARATION COMPLETED SUCCESSFULLY!")
print("Training and testing datasets saved.")
