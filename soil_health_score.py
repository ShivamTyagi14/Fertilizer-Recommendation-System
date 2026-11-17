
import pandas as pd
import os

print("SOIL HEALTH SCORING SYSTEM")
print("========================================")

# STEP 1: LOAD CLASSIFIED SOIL DATA

data = pd.read_csv(
    "outputs/soil_analysis/soil_nutrient_classification.csv"
)

print("\nSoil data loaded successfully!")
print("Total samples:", len(data))


# STEP 2: DEFINE NUTRIENT SCORING

def nutrient_score(status):

    if status == "Low":
        return 0

    elif status == "Medium":
        return 50

    elif status == "High":
        return 100

    return 0


# STEP 3: DEFINE pH SCORING

def ph_score(status):

    if status == "Normal to saline":
        return 100

    elif status == "Acidic":
        return 50

    elif status == "Tending to become alkaline":
        return 50

    elif status == "Alkaline":
        return 0

    return 0


# STEP 4: DEFINE EC SCORING

def ec_score(status):

    if status == "Normal":
        return 100

    elif status == "Critical for germination":
        return 50

    elif status == "Critical for growth of sensitive crops":
        return 25

    elif status == "Injurious to most crops":
        return 0

    return 0


# STEP 5: CALCULATE INDIVIDUAL PARAMETER SCORES

data["OC_Score"] = data["OC_Status"].apply(
    nutrient_score
)

data["Nitrogen_Score"] = data["Nitrogen_Status"].apply(
    nutrient_score
)

data["Phosphorus_Score"] = data["Phosphorus_Status"].apply(
    nutrient_score
)

data["Potassium_Score"] = data["Potassium_Status"].apply(
    nutrient_score
)

data["pH_Score"] = data["pH_Status"].apply(
    ph_score
)

data["EC_Score"] = data["EC_Status"].apply(
    ec_score
)


# STEP 6: CALCULATE OVERALL SOIL HEALTH SCORE

score_columns = [
    "OC_Score",
    "Nitrogen_Score",
    "Phosphorus_Score",
    "Potassium_Score",
    "pH_Score",
    "EC_Score"
]

# Equal-weight average of six parameter scores
data["Soil_Health_Score"] = (
    data[score_columns].mean(axis=1)
).round(2)


# STEP 7: CLASSIFY OVERALL SOIL HEALTH

def classify_soil_health(score):

    if score >= 80:
        return "Excellent"

    elif score >= 60:
        return "Good"

    elif score >= 40:
        return "Moderate"

    else:
        return "Poor"


data["Soil_Health_Category"] = (
    data["Soil_Health_Score"].apply(
        classify_soil_health
    )
)


# STEP 8: DISPLAY SAMPLE-WISE SCORES

print("\n========================================")
print("INDIVIDUAL SOIL HEALTH REPORT")
print("========================================")

display_columns = [
    "Sample",
    "OC_Score",
    "Nitrogen_Score",
    "Phosphorus_Score",
    "Potassium_Score",
    "pH_Score",
    "EC_Score",
    "Soil_Health_Score",
    "Soil_Health_Category"
]

print(
    data[display_columns].head(10).to_string(index=False)
)


# STEP 9: OVERALL HEALTH CATEGORY DISTRIBUTION

print("\n========================================")
print("SOIL HEALTH CATEGORY DISTRIBUTION")
print("========================================")

category_counts = data[
    "Soil_Health_Category"
].value_counts()

for category in [
    "Excellent", "Good", "Moderate", "Poor"
]:

    count = category_counts.get(category, 0)

    percentage = count / len(data) * 100

    print(
        category, ":",
        count,
        "samples (",
        round(percentage, 2),
        "%)"
    )


# STEP 10: AVERAGE SOIL HEALTH SCORE

average_score = data["Soil_Health_Score"].mean()

print("\nAverage Soil Health Score:",
      round(average_score, 2), "/ 100")


# STEP 11: SAVE RESULTS

os.makedirs("outputs/soil_analysis", exist_ok=True)

data.to_csv(
    "outputs/soil_analysis/soil_health_report.csv",
    index=False
)

category_counts.to_csv(
    "outputs/soil_analysis/soil_health_distribution.csv",
    header=["Number_of_Samples"]
)


# STEP 12: COMPLETION

print("\n========================================")
print("SOIL HEALTH ANALYSIS COMPLETED!")
print("========================================")

print("\nReports saved in outputs/soil_analysis/")

print("1. soil_health_report.csv")
print("2. soil_health_distribution.csv")
