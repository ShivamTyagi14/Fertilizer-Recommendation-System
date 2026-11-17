
import pandas as pd
import os

print("SMART SOIL NUTRIENT ANALYSIS SYSTEM")
print("========================================")

# STEP 1: LOAD CLEANED SOIL DATASET

data = pd.read_csv("data/processed/agrinet_cleaned.csv")

print("\nDataset loaded successfully!")
print("Total soil samples:", len(data))


# STEP 2: DEFINE NUTRIENT CLASSIFICATION FUNCTIONS

def classify_organic_carbon(value):

    if value < 0.5:
        return "Low"
    elif value <= 0.75:
        return "Medium"
    else:
        return "High"


def classify_nitrogen(value):

    if value < 240:
        return "Low"
    elif value <= 480:
        return "Medium"
    else:
        return "High"


def classify_phosphorus(value):

    if value < 11:
        return "Low"
    elif value <= 22:
        return "Medium"
    else:
        return "High"


def classify_potassium(value):

    if value < 110:
        return "Low"
    elif value <= 280:
        return "Medium"
    else:
        return "High"


# STEP 3: DEFINE SOIL PROPERTY CLASSIFICATION FUNCTIONS

def classify_ph(value):

    if value < 6.0:
        return "Acidic"
    elif value <= 8.5:
        return "Normal to saline"
    elif value <= 9.0:
        return "Tending to become alkaline"
    else:
        return "Alkaline"


def classify_ec(value):

    if value < 1:
        return "Normal"
    elif value < 2:
        return "Critical for germination"
    elif value <= 4:
        return "Critical for growth of sensitive crops"
    else:
        return "Injurious to most crops"


# STEP 4: APPLY CLASSIFICATION TO ALL SOIL SAMPLES

data["OC_Status"] = data["OC"].apply(
    classify_organic_carbon
)

data["Nitrogen_Status"] = data["N"].apply(
    classify_nitrogen
)

data["Phosphorus_Status"] = data["P"].apply(
    classify_phosphorus
)

data["Potassium_Status"] = data["K"].apply(
    classify_potassium
)

data["pH_Status"] = data["pH"].apply(
    classify_ph
)

data["EC_Status"] = data["EC"].apply(
    classify_ec
)


# STEP 5: DISPLAY FIRST FIVE CLASSIFIED SAMPLES

print("\n========================================")
print("SOIL SAMPLE CLASSIFICATION")
print("========================================")

columns_to_display = [
    "Sample",
    "pH",
    "pH_Status",
    "EC",
    "EC_Status",
    "OC",
    "OC_Status",
    "N",
    "Nitrogen_Status",
    "P",
    "Phosphorus_Status",
    "K",
    "Potassium_Status"
]

print(data[columns_to_display].head().to_string(index=False))


# STEP 6: GENERATE NUTRIENT STATUS SUMMARY

nutrients = {
    "Organic Carbon": "OC_Status",
    "Nitrogen": "Nitrogen_Status",
    "Phosphorus": "Phosphorus_Status",
    "Potassium": "Potassium_Status"
}

summary = []

print("\n========================================")
print("OVERALL NUTRIENT STATUS")
print("========================================")

for nutrient, column in nutrients.items():

    counts = data[column].value_counts()

    low = counts.get("Low", 0)
    medium = counts.get("Medium", 0)
    high = counts.get("High", 0)

    total = len(data)

    print("\n", nutrient)
    print("Low:", low)
    print("Medium:", medium)
    print("High:", high)

    summary.append({
        "Nutrient": nutrient,
        "Low Samples": low,
        "Medium Samples": medium,
        "High Samples": high,
        "Total Samples": total,
        "Low Percentage": round(low / total * 100, 2),
        "Medium Percentage": round(medium / total * 100, 2),
        "High Percentage": round(high / total * 100, 2)
    })


# STEP 7: GENERATE SOIL PROPERTY SUMMARY

print("\n========================================")
print("SOIL PROPERTY ANALYSIS")
print("========================================")

for property_name, column in [
    ("pH", "pH_Status"),
    ("EC", "EC_Status")
]:

    print("\n", property_name, "Classification")

    print(data[column].value_counts().to_string())


# STEP 8: IDENTIFY LOW NUTRIENT SAMPLES

print("\n========================================")
print("NUTRIENT DEFICIENCY ANALYSIS")
print("========================================")

low_nutrient_samples = data[
    (data["OC_Status"] == "Low") |
    (data["Nitrogen_Status"] == "Low") |
    (data["Phosphorus_Status"] == "Low") |
    (data["Potassium_Status"] == "Low")
]

print(
    "Samples with at least one low nutrient:",
    len(low_nutrient_samples)
)

print("\nFirst five samples with low nutrient levels:")

print(
    low_nutrient_samples[
        ["Sample", "OC_Status", "Nitrogen_Status",
         "Phosphorus_Status", "Potassium_Status"]
    ].head().to_string(index=False)
)


# STEP 9: SAVE ANALYSIS REPORTS

os.makedirs("outputs/soil_analysis", exist_ok=True)

# Save individual soil sample analysis
data.to_csv(
    "outputs/soil_analysis/soil_nutrient_classification.csv",
    index=False
)

# Save overall nutrient summary
summary_df = pd.DataFrame(summary)

summary_df.to_csv(
    "outputs/soil_analysis/nutrient_summary.csv",
    index=False
)

# Save samples with at least one low nutrient
low_nutrient_samples.to_csv(
    "outputs/soil_analysis/low_nutrient_samples.csv",
    index=False
)


# STEP 10: COMPLETION MESSAGE

print("\n========================================")
print("SOIL NUTRIENT ANALYSIS COMPLETED!")
print("========================================")

print("\nReports saved in:")
print("outputs/soil_analysis/")

print("\nGenerated files:")
print("1. soil_nutrient_classification.csv")
print("2. nutrient_summary.csv")
print("3. low_nutrient_samples.csv")
