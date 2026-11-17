
import os
import pandas as pd


# ==========================================
# STEP 1: DEFINE FILE PATHS
# ==========================================

RAW_SOIL_FILE = "data/processed/agrinet_cleaned.csv"

CLASSIFICATION_FILE = (
    "outputs/soil_analysis/soil_nutrient_classification.csv"
)

HEALTH_FILE = (
    "outputs/soil_analysis/soil_health_report.csv"
)

OUTPUT_FOLDER = "outputs/fertilizer_quantity"

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "soil_test_integration_report.csv"
)


# ==========================================
# STEP 2: LOAD SOIL DATA
# ==========================================

def load_soil_data():

    raw_df = pd.read_csv(RAW_SOIL_FILE)
    classification_df = pd.read_csv(CLASSIFICATION_FILE)
    health_df = pd.read_csv(HEALTH_FILE)

    required_columns = [
        "Sample", "pH", "EC", "OC", "N", "P", "K"
    ]

    for column in required_columns:

        if column not in raw_df.columns:
            raise ValueError(
                f"Missing column in raw soil file: {column}"
            )

    if "Sample" not in classification_df.columns:
        raise ValueError("Sample column missing in classification file.")

    if "Sample" not in health_df.columns:
        raise ValueError("Sample column missing in health report.")

    # Ensure each sample appears only once
    for name, df in [
        ("Raw soil data", raw_df),
        ("Classification data", classification_df),
        ("Soil health data", health_df)
    ]:

        if df["Sample"].duplicated().any():
            raise ValueError(
                f"Duplicate sample IDs found in {name}."
            )

    # Check whether all files contain the same sample IDs
    raw_samples = set(raw_df["Sample"])
    classification_samples = set(classification_df["Sample"])
    health_samples = set(health_df["Sample"])

    if not (
        raw_samples == classification_samples == health_samples
    ):
        raise ValueError(
            "Sample IDs do not match across the three files."
        )

    # Use the cleaned data as the base
    merged_df = raw_df.merge(
        classification_df[
            [
                "Sample",
                "OC_Status",
                "Nitrogen_Status",
                "Phosphorus_Status",
                "Potassium_Status",
                "pH_Status",
                "EC_Status"
            ]
        ],
        on="Sample",
        how="inner",
        validate="one_to_one"
    )

    merged_df = merged_df.merge(
        health_df[
            [
                "Sample",
                "Soil_Health_Score",
                "Soil_Health_Category"
            ]
        ],
        on="Sample",
        how="inner",
        validate="one_to_one"
    )

    return merged_df


# ==========================================
# STEP 3: GENERATE SOIL CONDITION EXPLANATION
# ==========================================

def generate_soil_explanation(sample):

    explanations = []

    # Organic Carbon
    if sample["OC_Status"] == "Low":
        explanations.append(
            "Organic carbon is classified as Low. "
            "Improving organic matter management may be beneficial."
        )

    # Nitrogen
    if sample["Nitrogen_Status"] == "Low":
        explanations.append(
            "Nitrogen is classified as Low according to the "
            "project's adopted threshold."
        )

    # Phosphorus
    if sample["Phosphorus_Status"] == "Low":
        explanations.append(
            "Phosphorus is classified as Low according to the "
            "project's adopted threshold."
        )

    # Potassium
    if sample["Potassium_Status"] == "Low":
        explanations.append(
            "Potassium is classified as Low according to the "
            "project's adopted threshold."
        )

    # Soil pH
    if sample["pH_Status"] != "Normal to saline":
        explanations.append(
            f"Soil pH condition: {sample['pH_Status']}."
        )

    # Soil EC
    if sample["EC_Status"] != "Normal":
        explanations.append(
            f"Soil electrical conductivity condition: "
            f"{sample['EC_Status']}."
        )

    if not explanations:
        explanations.append(
            "No low nutrient classification or pH/EC warning "
            "was found in the available report."
        )

    return " ".join(explanations)


# ==========================================
# STEP 4: SELECT A SOIL SAMPLE
# ==========================================

def select_sample(soil_df):

    print("\nAVAILABLE SOIL SAMPLES")
    print("=" * 50)

    for sample_id in soil_df["Sample"].tolist():
        print("-", sample_id)

    selected_sample = input(
        "\nEnter soil sample ID (example: Sample 1): "
    ).strip()

    selected_data = soil_df[
        soil_df["Sample"].str.lower()
        == selected_sample.lower()
    ]

    if selected_data.empty:
        print("\nInvalid sample ID. Please try again.")
        return None

    return selected_data.iloc[0]


# ==========================================
# STEP 5: DISPLAY SOIL TEST REPORT
# ==========================================

def display_report(sample):

    print("\n")
    print("=" * 60)
    print("       SOIL TEST INTEGRATION REPORT")
    print("=" * 60)

    print("Sample ID:", sample["Sample"])

    print("\nSOIL TEST VALUES")
    print("-" * 60)

    print("pH:", sample["pH"])
    print("EC:", sample["EC"])
    print("Organic Carbon:", sample["OC"])
    print("Nitrogen:", sample["N"])
    print("Phosphorus:", sample["P"])
    print("Potassium:", sample["K"])

    print("\nNUTRIENT CLASSIFICATION")
    print("-" * 60)

    print("Organic Carbon:", sample["OC_Status"])
    print("Nitrogen:", sample["Nitrogen_Status"])
    print("Phosphorus:", sample["Phosphorus_Status"])
    print("Potassium:", sample["Potassium_Status"])

    print("\nOTHER SOIL CONDITIONS")
    print("-" * 60)

    print("pH Status:", sample["pH_Status"])
    print("EC Status:", sample["EC_Status"])

    print("\nSOIL HEALTH")
    print("-" * 60)

    print(
        "Soil Health Score:",
        sample["Soil_Health_Score"],
        "/ 100"
    )

    print(
        "Soil Health Category:",
        sample["Soil_Health_Category"]
    )

    print("\nSOIL CONDITION EXPLANATION")
    print("-" * 60)

    explanation = generate_soil_explanation(sample)

    print(explanation)

    print("\nFERTILIZER QUANTITY ADJUSTMENT")
    print("-" * 60)

    print("Adjustment applied: NO")

    print(
        "Reason: Soil N, P and K units and laboratory methods "
        "have not yet been confirmed."
    )

    print(
        "The existing crop-based fertilizer quantity estimate "
        "remains unchanged."
    )

    print("\nIMPORTANT DATA LIMITATION")
    print("-" * 60)

    print(
        "The nutrient classifications use project-adopted "
        "thresholds. Their suitability for these laboratory "
        "measurements requires confirmation."
    )

    print(
        "Raw N, P and K values must not be directly deducted "
        "from crop nutrient requirements until their units, "
        "methods and interpretation are verified."
    )

    print("=" * 60)


# ==========================================
# STEP 6: SAVE REPORT
# ==========================================

def save_report(sample):

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    report = pd.DataFrame([{
        "Sample": sample["Sample"],
        "pH": sample["pH"],
        "EC": sample["EC"],
        "OC": sample["OC"],
        "N": sample["N"],
        "P": sample["P"],
        "K": sample["K"],
        "OC_Status": sample["OC_Status"],
        "Nitrogen_Status": sample["Nitrogen_Status"],
        "Phosphorus_Status": sample["Phosphorus_Status"],
        "Potassium_Status": sample["Potassium_Status"],
        "pH_Status": sample["pH_Status"],
        "EC_Status": sample["EC_Status"],
        "Soil_Health_Score": sample["Soil_Health_Score"],
        "Soil_Health_Category": sample["Soil_Health_Category"],
        "Soil_Condition_Explanation": generate_soil_explanation(sample),
        "Fertilizer_Quantity_Adjustment": "Not applied",
        "Adjustment_Reason": (
            "N, P and K units and laboratory methods are unverified."
        )
    }])

    report.to_csv(OUTPUT_FILE, index=False)

    print("\nReport saved successfully!")
    print("File:", OUTPUT_FILE)


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    try:

        soil_data = load_soil_data()

        print("\nSoil datasets loaded successfully!")
        print("Total available samples:", len(soil_data))

        selected_sample = select_sample(soil_data)

        if selected_sample is not None:

            display_report(selected_sample)
            save_report(selected_sample)

    except FileNotFoundError as error:

        print("\nFile not found:", error)

    except Exception as error:

        print("\nAn error occurred:", error)
