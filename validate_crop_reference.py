
import pandas as pd

file_path = "data/reference/crop_nutrient_requirements.csv"

data = pd.read_csv(file_path)

print("=" * 55)
print("CROP NUTRIENT REFERENCE TABLE VALIDATION")
print("=" * 55)

# Required columns
required_columns = [
    "crop_category",
    "representative_crop",
    "season",
    "N_kg_ha",
    "P2O5_kg_ha",
    "K2O_kg_ha",
    "region",
    "source",
    "status",
    "notes",
    "production_condition"
]

missing_columns = [
    col for col in required_columns if col not in data.columns
]

if missing_columns:
    print("Missing columns:", missing_columns)
else:
    print("All required columns are present.")

# Check crop categories
expected_crops = [
    "Barley", "Cotton", "Ground Nuts", "Maize",
    "Millets", "Oil seeds", "Paddy", "Pulses",
    "Sugarcane", "Tobacco"
]

available_crops = data["crop_category"].dropna().unique()

print("\nCROP CATEGORY CHECK")
for crop in expected_crops:
    if crop in available_crops:
        print(crop, ": Available")
    else:
        print(crop, ": MISSING")

# Check missing nutrient values
nutrient_columns = ["N_kg_ha", "P2O5_kg_ha", "K2O_kg_ha"]

data["complete_npk"] = data[nutrient_columns].notna().all(axis=1)

print("\nNUTRIENT COMPLETENESS")
print("Complete NPK records:", data["complete_npk"].sum())
print("Incomplete NPK records:", (~data["complete_npk"]).sum())

# Check eligible complete records
eligible_statuses = ["Verified", "Regional reference"]

eligible = data[
    data["status"].isin(eligible_statuses) &
    data["complete_npk"]
]

print("\nCOMPLETE REFERENCE RECORDS")
print(eligible[
    [
        "crop_category",
        "representative_crop",
        "season",
        "production_condition",
        "N_kg_ha",
        "P2O5_kg_ha",
        "K2O_kg_ha",
        "region",
        "status"
    ]
].to_string(index=False))

# Check invalid negative nutrient values
negative_values = (
    data[nutrient_columns].lt(0).any(axis=1)
)

print("\nDATA QUALITY CHECK")
print("Negative nutrient records:", negative_values.sum())

# Save validation report
data.to_csv(
    "data/reference/crop_nutrient_validation.csv",
    index=False
)

print("\nTotal records:", len(data))
print("Validation report saved successfully.")
print("=" * 55)
