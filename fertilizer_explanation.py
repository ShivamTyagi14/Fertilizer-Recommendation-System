
import pandas as pd
import os

# ==========================================
# 1. FILE PATHS
# ==========================================

COMPOSITION_FILE = "data/reference/fertilizer_composition.csv"

QUANTITY_FILE = (
    "outputs/fertilizer_quantity/"
    "fertilizer_combination_comparison.csv"
)

OUTPUT_FOLDER = "outputs/fertilizer_explanation"

CSV_OUTPUT = os.path.join(
    OUTPUT_FOLDER,
    "fertilizer_explanation_report.csv"
)

TEXT_OUTPUT = os.path.join(
    OUTPUT_FOLDER,
    "fertilizer_explanation.txt"
)


# ==========================================
# 2. LOAD DATA
# ==========================================

def load_data():

    if not os.path.exists(COMPOSITION_FILE):
        raise FileNotFoundError(COMPOSITION_FILE)

    if not os.path.exists(QUANTITY_FILE):
        raise FileNotFoundError(QUANTITY_FILE)

    composition = pd.read_csv(COMPOSITION_FILE)
    quantity = pd.read_csv(QUANTITY_FILE)

    required_composition = [
        "fertilizer_name",
        "N_percent",
        "P2O5_percent",
        "K2O_percent",
        "S_percent"
    ]

    required_quantity = [
        "crop_category",
        "representative_crop",
        "season",
        "region",
        "area_acres",
        "combination",
        "phosphorus_fertilizer",
        "phosphorus_fertilizer_kg",
        "urea_kg",
        "mop_kg",
        "nitrogen_required_kg",
        "nitrogen_supplied_kg",
        "phosphorus_required_kg",
        "phosphorus_supplied_kg",
        "potassium_required_kg",
        "potassium_supplied_kg",
        "sulphur_supplied_kg"
    ]

    for column in required_composition:
        if column not in composition.columns:
            raise ValueError(
                f"Missing composition column: {column}"
            )

    for column in required_quantity:
        if column not in quantity.columns:
            raise ValueError(
                f"Missing quantity column: {column}"
            )

    return composition, quantity


# ==========================================
# 3. GET FERTILIZER COMPOSITION
# ==========================================

def get_fertilizer_composition(name, composition):

    matching = composition[
        composition["fertilizer_name"].str.strip().str.lower()
        == str(name).strip().lower()
    ]

    if matching.empty:
        raise ValueError(
            f"Composition not found for {name}"
        )

    row = matching.iloc[0]

    nutrient_columns = [
        "N_percent",
        "P2O5_percent",
        "K2O_percent",
        "S_percent"
    ]

    values = {}

    for column in nutrient_columns:

        value = pd.to_numeric(
            pd.Series([row[column]]),
            errors="coerce"
        ).iloc[0]

        if pd.isna(value):
            raise ValueError(
                f"Invalid {column} for {name}"
            )

        values[column] = float(value)

    return values


# ==========================================
# 4. CALCULATE NUTRIENT CONTRIBUTION
# ==========================================

def calculate_contribution(
    fertilizer_name,
    quantity_kg,
    composition
):

    nutrients = get_fertilizer_composition(
        fertilizer_name,
        composition
    )

    result = {}

    for nutrient, percentage in nutrients.items():

        result[nutrient] = (
            float(quantity_kg) * percentage / 100
        )

    return result


# ==========================================
# 5. EXPLAIN ONE COMBINATION
# ==========================================

def explain_combination(row, composition):

    phosphorus_fertilizer = row[
        "phosphorus_fertilizer"
    ]

    fertilizers = [
        (
            phosphorus_fertilizer,
            row["phosphorus_fertilizer_kg"]
        ),
        ("Urea", row["urea_kg"]),
        ("MOP", row["mop_kg"])
    ]

    totals = {
        "N_percent": 0.0,
        "P2O5_percent": 0.0,
        "K2O_percent": 0.0,
        "S_percent": 0.0
    }

    details = []

    for name, quantity in fertilizers:

        contribution = calculate_contribution(
            name,
            quantity,
            composition
        )

        for nutrient in totals:
            totals[nutrient] += contribution[nutrient]

        details.append({
            "name": name,
            "quantity": float(quantity),
            "contribution": contribution
        })

    # Crop nutrient requirements

    required = {
        "N_percent": float(row["nitrogen_required_kg"]),
        "P2O5_percent": float(row["phosphorus_required_kg"]),
        "K2O_percent": float(row["potassium_required_kg"])
    }

    differences = {}

    for nutrient in required:

        differences[nutrient] = (
            totals[nutrient] - required[nutrient]
        )

    return details, totals, required, differences


# ==========================================
# 6. GENERATE EXPLANATION
# ==========================================

def generate_explanation(
    row,
    details,
    totals,
    required,
    differences
):

    explanation = []

    explanation.append("=" * 65)
    explanation.append("FERTILIZER RECOMMENDATION EXPLANATION")
    explanation.append("=" * 65)

    explanation.append(
        f"Crop: {row['representative_crop']}"
    )

    explanation.append(
        f"Crop category: {row['crop_category']}"
    )

    explanation.append(
        f"Season: {row['season']}"
    )

    explanation.append(
        f"Region: {row['region']}"
    )

    explanation.append(
        f"Land area: {float(row['area_acres']):.2f} acres"
    )

    explanation.append(
        f"Selected combination: {row['combination']}"
    )

    explanation.append("\n1. WHY IS THIS COMBINATION USED?")

    explanation.append(
        "The selected combination uses different fertilizer "
        "products to supply the crop's required nutrients."
    )

    explanation.append("\n2. FERTILIZER-WISE EXPLANATION")

    for item in details:

        name = item["name"]
        quantity = item["quantity"]
        contribution = item["contribution"]

        explanation.append(
            f"\n{name}: {quantity:.2f} kg"
        )

        explanation.append(
            f"  Nitrogen supplied: "
            f"{contribution['N_percent']:.2f} kg"
        )

        explanation.append(
            f"  P2O5 supplied: "
            f"{contribution['P2O5_percent']:.2f} kg"
        )

        explanation.append(
            f"  K2O supplied: "
            f"{contribution['K2O_percent']:.2f} kg"
        )

        explanation.append(
            f"  Sulphur supplied: "
            f"{contribution['S_percent']:.2f} kg"
        )

    explanation.append("\n3. CROP NUTRIENT REQUIREMENTS")

    nutrient_names = {
        "N_percent": "Nitrogen",
        "P2O5_percent": "Phosphorus (P2O5)",
        "K2O_percent": "Potassium (K2O)"
    }

    for nutrient, label in nutrient_names.items():

        explanation.append(
            f"{label}: {required[nutrient]:.2f} kg required, "
            f"{totals[nutrient]:.2f} kg supplied"
        )

    explanation.append("\n4. WHY EACH FERTILIZER IS INCLUDED")

    explanation.append(
        f"{row['phosphorus_fertilizer']} supplies "
        "the phosphorus requirement."
    )

    explanation.append(
        "Urea supplies additional nitrogen."
    )

    explanation.append(
        "MOP supplies potassium."
    )

    if totals["S_percent"] > 0:

        explanation.append(
            f"This combination also supplies "
            f"{totals['S_percent']:.2f} kg of sulphur."
        )

    explanation.append("\n5. NUTRIENT BALANCE CHECK")

    for nutrient, label in nutrient_names.items():

        difference = differences[nutrient]

        explanation.append(
            f"{label} difference: {difference:+.2f} kg"
        )

    explanation.append("\n6. IMPORTANT LIMITATIONS")

    explanation.append(
        "This is a baseline nutrient-based calculation."
    )

    explanation.append(
        "It does not deduct nutrients already available "
        "in the soil."
    )

    explanation.append(
        "It does not calculate fertilizer application timing "
        "or split doses."
    )

    explanation.append(
        "It does not account for nutrient-use efficiency "
        "or crop-specific additional nutrient needs."
    )

    explanation.append(
        "Verify the recommendation with local agricultural "
        "experts before actual field application."
    )

    explanation.append("\n" + "=" * 65)

    return "\n".join(explanation)


# ==========================================
# 7. SAVE EXPLANATION REPORTS
# ==========================================

def save_reports(results, explanations):

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    results.to_csv(
        CSV_OUTPUT,
        index=False
    )

    with open(
        TEXT_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        for explanation in explanations:

            file.write(explanation)
            file.write("\n\n")

    print("\nEXPLANATION REPORTS SAVED")
    print("CSV:", CSV_OUTPUT)
    print("Text:", TEXT_OUTPUT)


# ==========================================
# 8. MAIN PROGRAM
# ==========================================

def main():

    print("=" * 65)
    print("FERTILIZER RECOMMENDATION EXPLANATION SYSTEM")
    print("=" * 65)

    composition, quantity = load_data()

    print("\nAvailable combinations:")

    for index, row in quantity.iterrows():

        print(
            f"{index + 1}. {row['combination']}"
        )

    try:

        choice = int(
            input("\nSelect combination number: ")
        )

        if choice < 1 or choice > len(quantity):
            print("Invalid selection.")
            return

    except ValueError:

        print("Please enter a valid number.")
        return

    selected = quantity.iloc[choice - 1]

    details, totals, required, differences = (
        explain_combination(selected, composition)
    )

    explanation = generate_explanation(
        selected,
        details,
        totals,
        required,
        differences
    )

    print("\n")
    print(explanation)

    results = pd.DataFrame([{
        "crop": selected["representative_crop"],
        "season": selected["season"],
        "combination": selected["combination"],
        "area_acres": selected["area_acres"],
        "nitrogen_required_kg": required["N_percent"],
        "nitrogen_supplied_kg": totals["N_percent"],
        "phosphorus_required_kg": required["P2O5_percent"],
        "phosphorus_supplied_kg": totals["P2O5_percent"],
        "potassium_required_kg": required["K2O_percent"],
        "potassium_supplied_kg": totals["K2O_percent"],
        "sulphur_supplied_kg": totals["S_percent"]
    }])

    save_reports(
        results,
        [explanation]
    )

    print("\nEXPLANATION GENERATED SUCCESSFULLY!")


# ==========================================
# 9. PROGRAM EXECUTION
# ==========================================

if __name__ == "__main__":
    main()
