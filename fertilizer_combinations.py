
import pandas as pd
import os

# ==========================================
# FILE PATHS
# ==========================================

CROP_FILE = "data/reference/crop_nutrient_requirements.csv"
FERTILIZER_FILE = "data/reference/fertilizer_composition.csv"

OUTPUT_FOLDER = "outputs/fertilizer_quantity"
OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "fertilizer_combination_comparison.csv"
)

ACRES_PER_HECTARE = 2.47105


# ==========================================
# 1. GET CROP REQUIREMENTS
# ==========================================

def get_crop_requirement(crop, season, condition):

    df = pd.read_csv(CROP_FILE)

    text_columns = [
        "crop_category",
        "season",
        "production_condition",
        "status"
    ]

    for col in text_columns:
        df[col] = df[col].astype(str).str.strip()

    selected = df[
        (df["crop_category"].str.lower() == crop.lower()) &
        (df["season"].str.lower() == season.lower()) &
        (df["status"].isin(["Verified", "Regional reference"]))
    ]

    # Prefer the exact production condition.
    # If unavailable, use Not specified.
    exact = selected[
        selected["production_condition"].str.lower()
        == condition.lower()
    ]

    if len(exact) > 0:
        selected = exact
    else:
        selected = selected[
            selected["production_condition"].str.lower()
            == "not specified"
        ]

    selected = selected.dropna(
        subset=["N_kg_ha", "P2O5_kg_ha", "K2O_kg_ha"]
    )

    if len(selected) != 1:

        print("\nUnable to identify exactly one crop reference.")

        if len(selected) > 1:
            print(selected[[
                "representative_crop",
                "production_condition",
                "region",
                "source"
            ]].to_string(index=False))

        return None

    return selected.iloc[0]


# ==========================================
# 2. LOAD FERTILIZER COMPOSITION
# ==========================================

def load_composition():

    df = pd.read_csv(FERTILIZER_FILE)

    df["fertilizer_name"] = (
        df["fertilizer_name"].str.strip()
    )

    return df.set_index("fertilizer_name")


# ==========================================
# 3. CALCULATE ONE COMBINATION
# ==========================================

def calculate_combination(
    name,
    phosphorus_source,
    n_required,
    p_required,
    k_required,
    area_hectares,
    composition
):

    # Convert nutrient requirements into total kg
    total_n = n_required * area_hectares
    total_p = p_required * area_hectares
    total_k = k_required * area_hectares

    # Get fertilizer nutrient percentages
    p_grade = composition.loc[
        phosphorus_source, "P2O5_percent"
    ]

    p_n_grade = composition.loc[
        phosphorus_source, "N_percent"
    ]

    p_s_grade = composition.loc[
        phosphorus_source, "S_percent"
    ]

    urea_grade = composition.loc[
        "Urea", "N_percent"
    ]

    mop_grade = composition.loc[
        "MOP", "K2O_percent"
    ]

    # Check that required nutrient grades are valid
    if p_grade <= 0 or urea_grade <= 0 or mop_grade <= 0:
        raise ValueError("Invalid fertilizer nutrient grade.")

    # Calculate phosphorus fertilizer quantity
    phosphorus_quantity = total_p * 100 / p_grade

    # Calculate nitrogen supplied by phosphorus fertilizer
    nitrogen_from_phosphorus_fertilizer = (
        phosphorus_quantity * p_n_grade / 100
    )

    # Calculate remaining nitrogen
    remaining_n = max(
        0,
        total_n - nitrogen_from_phosphorus_fertilizer
    )

    # Calculate Urea
    urea_quantity = remaining_n * 100 / urea_grade

    # Calculate MOP
    mop_quantity = total_k * 100 / mop_grade

    # Actual nutrients supplied
    actual_n = (
        phosphorus_quantity * p_n_grade / 100
        + urea_quantity * urea_grade / 100
    )

    actual_p = phosphorus_quantity * p_grade / 100

    actual_k = mop_quantity * mop_grade / 100

    actual_s = phosphorus_quantity * p_s_grade / 100

    return {
        "combination": name,
        "phosphorus_fertilizer": phosphorus_source,
        "phosphorus_fertilizer_kg": phosphorus_quantity,
        "urea_kg": urea_quantity,
        "mop_kg": mop_quantity,
        "total_fertilizer_kg": (
            phosphorus_quantity +
            urea_quantity +
            mop_quantity
        ),
        "nitrogen_required_kg": total_n,
        "nitrogen_supplied_kg": actual_n,
        "phosphorus_required_kg": total_p,
        "phosphorus_supplied_kg": actual_p,
        "potassium_required_kg": total_k,
        "potassium_supplied_kg": actual_k,
        "sulphur_supplied_kg": actual_s,
        "nitrogen_difference_kg": actual_n - total_n,
        "phosphorus_difference_kg": actual_p - total_p,
        "potassium_difference_kg": actual_k - total_k
    }


# ==========================================
# 4. MAIN PROGRAM
# ==========================================

def main():

    print("=" * 60)
    print("MULTIPLE FERTILIZER COMBINATION CALCULATOR")
    print("=" * 60)

    crop = input("Enter crop category: ").strip()
    season = input("Enter season (Kharif/Rabi): ").strip()
    condition = input(
        "Enter production condition: "
    ).strip()

    try:

        area = float(
            input("Enter land area in acres: ")
        )

        if area <= 0:
            print("Land area must be greater than zero.")
            return

    except ValueError:

        print("Please enter a valid land area.")
        return

    # Get crop data
    crop_data = get_crop_requirement(
        crop, season, condition
    )

    if crop_data is None:
        print("\nCrop reference not available.")
        return

    # Load fertilizer data
    composition = load_composition()

    required_products = [
        "DAP",
        "SSP",
        "TSP",
        "Urea",
        "MOP"
    ]

    for product in required_products:

        if product not in composition.index:
            print("Missing composition:", product)
            return

    # Convert area
    area_hectares = area / ACRES_PER_HECTARE

    # Three fertilizer combinations
    combinations = [
        ("Combination A - DAP based", "DAP"),
        ("Combination B - SSP based", "SSP"),
        ("Combination C - TSP based", "TSP")
    ]

    results = []

    for name, phosphorus_source in combinations:

        result = calculate_combination(
            name,
            phosphorus_source,
            crop_data["N_kg_ha"],
            crop_data["P2O5_kg_ha"],
            crop_data["K2O_kg_ha"],
            area_hectares,
            composition
        )

        results.append(result)

    # Display crop reference
    print("\n" + "=" * 60)
    print("CROP REFERENCE")
    print("=" * 60)

    print("Crop:", crop_data["representative_crop"])
    print("Region:", crop_data["region"])
    print("Season:", crop_data["season"])
    print("Source:", crop_data["source"])
    print("Status:", crop_data["status"])

    print(f"Land area: {area:.2f} acres")
    print(f"Land area: {area_hectares:.4f} hectares")

    # Display comparison
    print("\n" + "=" * 60)
    print("FERTILIZER COMBINATION COMPARISON")
    print("=" * 60)

    for result in results:

        print("\n" + result["combination"])

        print(
            f"{result['phosphorus_fertilizer']}: "
            f"{result['phosphorus_fertilizer_kg']:.2f} kg"
        )

        print(f"Urea: {result['urea_kg']:.2f} kg")
        print(f"MOP: {result['mop_kg']:.2f} kg")

        print(
            f"Total fertilizer: "
            f"{result['total_fertilizer_kg']:.2f} kg"
        )

        print(
            f"N supplied: {result['nitrogen_supplied_kg']:.2f} kg"
        )

        print(
            f"P2O5 supplied: "
            f"{result['phosphorus_supplied_kg']:.2f} kg"
        )

        print(
            f"K2O supplied: "
            f"{result['potassium_supplied_kg']:.2f} kg"
        )

        print(
            f"S supplied: {result['sulphur_supplied_kg']:.2f} kg"
        )

    # Save comparison report
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    report = pd.DataFrame(results)

    report.insert(0, "crop_category", crop_data["crop_category"])
    report.insert(1, "representative_crop",
                  crop_data["representative_crop"])
    report.insert(2, "season", crop_data["season"])
    report.insert(3, "region", crop_data["region"])
    report.insert(4, "area_acres", area)

    report.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 60)
    print("COMPARISON REPORT SAVED")
    print("=" * 60)

    print("File:", OUTPUT_FILE)

    print("\nCalculation completed successfully.")


# ==========================================
# 5. PROGRAM EXECUTION
# ==========================================

if __name__ == "__main__":
    main()
