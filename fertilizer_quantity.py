
import pandas as pd
import os

# ==========================================
# FILE PATHS AND SETTINGS
# ==========================================

CROP_FILE = "data/reference/crop_nutrient_requirements.csv"
FERTILIZER_FILE = "data/reference/fertilizer_composition.csv"

OUTPUT_FOLDER = "outputs/fertilizer_quantity"
OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "fertilizer_quantity_report.csv"
)

# 1 hectare = 2.47105 acres
ACRES_PER_HECTARE = 2.47105


# ==========================================
# 1. GET CROP NUTRIENT REQUIREMENTS
# ==========================================

def get_crop_requirement(crop, season, production_condition):

    crops = pd.read_csv(CROP_FILE)

    # Clean text columns
    text_columns = [
        "crop_category",
        "season",
        "production_condition",
        "status"
    ]

    for col in text_columns:
        crops[col] = crops[col].astype(str).str.strip()

    # Match crop and season
    selected = crops[
        (crops["crop_category"].str.lower() == crop.lower()) &
        (crops["season"].str.lower() == season.lower()) &
        (crops["status"].isin(
            ["Verified", "Regional reference"]
        ))
    ]

    # Match production condition
    condition = production_condition.strip().lower()

    selected = selected[
        (selected["production_condition"].str.lower() == condition) |
        (selected["production_condition"].str.lower() == "not specified")
    ]

    # Keep records with complete nutrient requirements
    selected = selected.dropna(
        subset=["N_kg_ha", "P2O5_kg_ha", "K2O_kg_ha"]
    )

    if len(selected) == 0:
        return None

    if len(selected) > 1:

        print("\nMultiple crop reference records found.")

        print(selected[[
            "representative_crop",
            "season",
            "production_condition",
            "N_kg_ha",
            "P2O5_kg_ha",
            "K2O_kg_ha",
            "region",
            "source"
        ]].to_string(index=False))

        return None

    return selected.iloc[0]


# ==========================================
# 2. LOAD FERTILIZER COMPOSITION
# ==========================================

def get_fertilizer_composition():

    fertilizers = pd.read_csv(FERTILIZER_FILE)

    fertilizers["fertilizer_name"] = (
        fertilizers["fertilizer_name"].str.strip()
    )

    return fertilizers.set_index("fertilizer_name")


# ==========================================
# 3. CALCULATE FERTILIZER QUANTITIES
# ==========================================

def calculate_quantity(n, p2o5, k2o, area_acres):

    # Convert acres into hectares
    area_hectares = area_acres / ACRES_PER_HECTARE

    # Calculate total nutrient requirements
    total_n = n * area_hectares
    total_p2o5 = p2o5 * area_hectares
    total_k2o = k2o * area_hectares

    # DAP contains 18% nitrogen and 46% P2O5
    dap_quantity = total_p2o5 * 100 / 46

    # Nitrogen supplied by DAP
    nitrogen_from_dap = dap_quantity * 18 / 100

    # Remaining nitrogen requirement
    remaining_n = max(
        0,
        total_n - nitrogen_from_dap
    )

    # Urea contains 46% nitrogen
    urea_quantity = remaining_n * 100 / 46

    # MOP contains 60% K2O
    mop_quantity = total_k2o * 100 / 60

    return {
        "area_hectares": area_hectares,
        "required_nitrogen_kg": total_n,
        "required_phosphorus_kg": total_p2o5,
        "required_potassium_kg": total_k2o,
        "dap_kg": dap_quantity,
        "nitrogen_from_dap_kg": nitrogen_from_dap,
        "urea_kg": urea_quantity,
        "mop_kg": mop_quantity
    }


# ==========================================
# 4. SAVE QUANTITY REPORT
# ==========================================

def save_quantity_report(crop_data, area, result):

    # Create output folder if it does not exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    report = {
        "crop_category": crop_data["crop_category"],
        "representative_crop": crop_data["representative_crop"],
        "season": crop_data["season"],
        "production_condition": crop_data["production_condition"],
        "region": crop_data["region"],
        "source": crop_data["source"],
        "reference_status": crop_data["status"],

        "area_acres": area,
        "area_hectares": result["area_hectares"],

        "nitrogen_required_kg": result["required_nitrogen_kg"],
        "P2O5_required_kg": result["required_phosphorus_kg"],
        "K2O_required_kg": result["required_potassium_kg"],

        "DAP_kg": result["dap_kg"],
        "nitrogen_from_DAP_kg": result["nitrogen_from_dap_kg"],
        "Urea_kg": result["urea_kg"],
        "MOP_kg": result["mop_kg"]
    }

    df = pd.DataFrame([report])

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nQuantity report saved successfully!")
    print("File:", OUTPUT_FILE)


# ==========================================
# 5. MAIN PROGRAM
# ==========================================

def main():

    print("=" * 55)
    print("FERTILIZER QUANTITY ESTIMATION SYSTEM")
    print("=" * 55)

    # Get user inputs
    crop = input("Enter crop category: ").strip()

    season = input(
        "Enter season (Kharif/Rabi): "
    ).strip()

    condition = input(
        "Enter production condition: "
    ).strip()

    # Get land area
    try:

        area = float(
            input("Enter land area in acres: ")
        )

        if area <= 0:
            print("Area must be greater than zero.")
            return

    except ValueError:

        print("Please enter a valid numerical area.")
        return

    # Find crop nutrient reference
    crop_data = get_crop_requirement(
        crop,
        season,
        condition
    )

    if crop_data is None:

        print("\nNo single eligible crop reference was found.")
        print("Check crop, season and production condition.")

        return

    # Load fertilizer composition
    composition = get_fertilizer_composition()

    # Verify required fertilizer grades
    expected = {
        "DAP": [18, 46, 0],
        "Urea": [46, 0, 0],
        "MOP": [0, 0, 60]
    }

    for product, grades in expected.items():

        if product not in composition.index:

            print("Missing fertilizer composition:", product)
            return

        actual = composition.loc[
            product,
            ["N_percent", "P2O5_percent", "K2O_percent"]
        ].tolist()

        if actual != grades:

            print("Fertilizer grade mismatch:", product)
            return

    # Calculate quantities
    result = calculate_quantity(
        crop_data["N_kg_ha"],
        crop_data["P2O5_kg_ha"],
        crop_data["K2O_kg_ha"],
        area
    )

    # ======================================
    # DISPLAY CROP REFERENCE
    # ======================================

    print("\n" + "=" * 55)
    print("CROP REFERENCE")
    print("=" * 55)

    print("Representative crop:",
          crop_data["representative_crop"])

    print("Region:", crop_data["region"])
    print("Source:", crop_data["source"])
    print("Reference status:", crop_data["status"])

    print("Production condition:",
          crop_data["production_condition"])

    # ======================================
    # DISPLAY NUTRIENT REQUIREMENTS
    # ======================================

    print("\n" + "=" * 55)
    print("NUTRIENT REQUIREMENTS")
    print("=" * 55)

    print(f"Land area: {area:.2f} acres")

    print(
        f"Land area: {result['area_hectares']:.4f} hectares"
    )

    print(
        f"Nitrogen: {result['required_nitrogen_kg']:.2f} kg"
    )

    print(
        f"P2O5: {result['required_phosphorus_kg']:.2f} kg"
    )

    print(
        f"K2O: {result['required_potassium_kg']:.2f} kg"
    )

    # ======================================
    # DISPLAY FERTILIZER QUANTITIES
    # ======================================

    print("\n" + "=" * 55)
    print("ESTIMATED FERTILIZER QUANTITIES")
    print("=" * 55)

    print(f"DAP: {result['dap_kg']:.2f} kg")

    print(
        "Nitrogen supplied by DAP:",
        f"{result['nitrogen_from_dap_kg']:.2f} kg"
    )

    print(f"Urea: {result['urea_kg']:.2f} kg")

    print(f"MOP: {result['mop_kg']:.2f} kg")

    # ======================================
    # SAVE REPORT
    # ======================================

    save_quantity_report(
        crop_data,
        area,
        result
    )

    # ======================================
    # IMPORTANT NOTE
    # ======================================

    print("\n" + "=" * 55)
    print("IMPORTANT NOTE")
    print("=" * 55)

    print("These are baseline nutrient-based estimates.")
    print("They are not final soil-test-based prescriptions.")
    print("Verify local agronomic recommendations before application.")

    print("\nQUANTITY ESTIMATION COMPLETED!")


# ==========================================
# 6. PROGRAM EXECUTION
# ==========================================

if __name__ == "__main__":
    main()
