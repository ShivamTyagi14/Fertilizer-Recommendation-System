
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

print("EXPLORATORY DATA ANALYSIS")
print("==============================")

# Load cleaned datasets
fertilizer_data = pd.read_csv(
    "data/processed/fertilizer_cleaned.csv"
)

soil_data = pd.read_csv(
    "data/processed/agrinet_cleaned.csv"
)

os.makedirs("outputs/graphs", exist_ok=True)


# =================================
# 1. FERTILIZER DATASET ANALYSIS
# =================================

print("\n1. FERTILIZER DATASET ANALYSIS")

print("\nDataset Shape:")
print(fertilizer_data.shape)

print("\nStatistical Information:")
print(fertilizer_data.describe(include="all"))

print("\nFertilizer Distribution:")
print(fertilizer_data["Fertilizer"].value_counts())

print("\nSoil Type Distribution:")
print(fertilizer_data["Soil_Type"].value_counts())

print("\nCrop Type Distribution:")
print(fertilizer_data["Crop_Type"].value_counts())


# Graph 1: Fertilizer Distribution
plt.figure(figsize=(12, 6))

sns.countplot(
    data=fertilizer_data,
    x="Fertilizer",
    order=fertilizer_data["Fertilizer"].value_counts().index
)

plt.title("Distribution of Fertilizer Types")
plt.xlabel("Fertilizer")
plt.ylabel("Number of Records")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig("outputs/graphs/fertilizer_distribution.png")
plt.close()


# Graph 2: Soil Type Distribution
plt.figure(figsize=(8, 5))

sns.countplot(data=fertilizer_data, x="Soil_Type")

plt.title("Distribution of Soil Types")
plt.xlabel("Soil Type")
plt.ylabel("Number of Records")
plt.tight_layout()

plt.savefig("outputs/graphs/soil_distribution.png")
plt.close()


# Graph 3: Crop Type Distribution
plt.figure(figsize=(12, 6))

sns.countplot(data=fertilizer_data, x="Crop_Type")

plt.title("Distribution of Crop Types")
plt.xlabel("Crop Type")
plt.ylabel("Number of Records")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig("outputs/graphs/crop_distribution.png")
plt.close()


# =================================
# 2. AGRINET SOIL DATASET ANALYSIS
# =================================

print("\n2. AGRINET SOIL DATASET ANALYSIS")

print("\nDataset Shape:")
print(soil_data.shape)

print("\nStatistical Information:")
print(soil_data.describe())

# Soil nutrient columns
nutrient_columns = [
    "pH", "EC", "OC", "N", "P", "K",
    "S", "Zn", "B", "Fe", "Mn", "Cu"
]

print("\nSoil Nutrient Statistics:")
print(soil_data[nutrient_columns].describe())


# Graph 4: Soil Nutrient Distribution
soil_data[nutrient_columns].hist(
    figsize=(14, 12),
    bins=15
)

plt.suptitle("Distribution of Soil Nutrients")
plt.tight_layout()

plt.savefig("outputs/graphs/soil_nutrient_distribution.png")
plt.close()


# Graph 5: Nutrient Correlation Heatmap
plt.figure(figsize=(12, 8))

correlation = soil_data[nutrient_columns].corr()

sns.heatmap(
    correlation,
    annot=True,
    cmap="coolwarm",
    fmt=".2f"
)

plt.title("Soil Nutrient Correlation Heatmap")
plt.tight_layout()

plt.savefig("outputs/graphs/nutrient_correlation.png")
plt.close()


print("\n==============================")
print("EDA COMPLETED SUCCESSFULLY!")
print("All graphs saved in outputs/graphs/")
