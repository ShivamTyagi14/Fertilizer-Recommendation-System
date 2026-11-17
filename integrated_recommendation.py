
import os
import joblib
import pandas as pd

# =====================================================
# 1. FILE PATHS AND SETTINGS
# =====================================================

SOIL_FILE = "outputs/fertilizer_quantity/soil_test_integration_report.csv"

CROP_FILE = "data/reference/crop_nutrient_requirements.csv"
COMPOSITION_FILE = "data/reference/fertilizer_composition.csv"
PRICE_FILE = "data/reference/fertilizer_prices.csv"

MODEL_FILE = "models/best_model.pkl"
PREPROCESSOR_FILE = "models/preprocessor.pkl"

ML_DATA_FILE = "data/processed/fertilizer_cleaned.csv"
MAPPING_FILE = "data/reference/fertilizer_label_mapping.csv"

OUTPUT_DIR = "outputs/integrated_recommendation"

QUANTITY_DIR = "outputs/fertilizer_quantity"
COST_DIR = "outputs/fertilizer_cost"
EXPLANATION_DIR = "outputs/fertilizer_explanation"

ACRES_PER_HECTARE = 2.47105


# =====================================================
# 2. GENERAL INPUT FUNCTIONS
# =====================================================

def get_number(message, minimum=None):

    while True:

        try:

            value = float(input(message))

            if minimum is not None and value <= minimum:
                print(f"Value must be greater than {minimum}.")
                continue

            return value

        except ValueError:

            print("Please enter a valid number.")


def get_choice(message, choices):

    choices = list(choices)

    print("\nAvailable options:")

    for choice in choices:
        print("-", choice)

    while True:

        value = input(message).strip()

        for choice in choices:

            if value.lower() == str(choice).lower():
                return choice

        print("Please select one of the available options.")


# =====================================================
# 3. LOAD PROJECT DATA
# =====================================================


def load_project_data():

    files = {
        "Soil report": SOIL_FILE,
        "Crop reference": CROP_FILE,
        "Fertilizer composition": COMPOSITION_FILE,
        "Fertilizer prices": PRICE_FILE,
        "ML model": MODEL_FILE,
        "Preprocessor": PREPROCESSOR_FILE,
        "ML dataset": ML_DATA_FILE,
        "Label mapping": MAPPING_FILE
    }

    for name, path in files.items():

        if not os.path.exists(path):

            raise FileNotFoundError(
                f"{name} file not found: {path}"
            )

    soil = pd.read_csv(SOIL_FILE)
    crops = pd.read_csv(CROP_FILE)
    composition = pd.read_csv(COMPOSITION_FILE)

    # Use fertilizer names as the index for calculations
    composition["fertilizer_name"] = (
        composition["fertilizer_name"].astype(str).str.strip()
    )

    composition = composition.set_index(
        "fertilizer_name",
        drop=False
    )

    prices = pd.read_csv(PRICE_FILE)
    ml_data = pd.read_csv(ML_DATA_FILE)
    mapping = pd.read_csv(MAPPING_FILE)

    model = joblib.load(MODEL_FILE)
    preprocessor = joblib.load(PREPROCESSOR_FILE)

    return (
        soil,
        crops,
        composition,
        prices,
        ml_data,
        mapping,
        model,
        preprocessor
    )



# =====================================================
# 4. SELECT SOIL SAMPLE
# =====================================================

def select_soil_sample(soil):

    print("\nAVAILABLE SOIL SAMPLES")
    print("-" * 55)

    for sample in soil["Sample"].head(10):
        print(sample)

    while True:

        sample_input = input(
            "\nEnter soil sample ID: "
        ).strip()

        if sample_input.isdigit():
            sample_input = "Sample " + sample_input

        selected = soil[
            soil["Sample"].astype(str).str.strip()
            == sample_input
        ]

        if not selected.empty:
            return selected.iloc[0]

        print("Invalid sample ID. Try again.")


# =====================================================
# 5. SELECT CROP AND AGRONOMIC DETAILS
# =====================================================


def select_crop_details(crops, ml_data):

    print("\n" + "=" * 65)
    print("CROP AND FARM DETAILS")
    print("=" * 65)

    ml_crops = sorted(
        ml_data["Crop_Type"].dropna().astype(str).str.strip().unique()
    )

    crop = get_choice(
        "Enter crop category: ",
        ml_crops
    )

    eligible = crops[
        (crops["crop_category"].astype(str).str.strip().str.lower()
         == crop.lower()) &
        (crops["status"].astype(str).str.strip().str.lower()
         .isin(["verified", "regional reference"]))
    ].copy()

    eligible = eligible.dropna(
        subset=["N_kg_ha", "P2O5_kg_ha", "K2O_kg_ha"]
    )

    if eligible.empty:
        raise ValueError(
            f"No complete eligible nutrient reference found for {crop}."
        )

    seasons = sorted(
        eligible["season"].dropna().astype(str).str.strip().unique()
    )

    season = get_choice(
        "Enter season: ",
        seasons
    )

    eligible = eligible[
        eligible["season"].astype(str).str.strip().str.lower()
        == season.lower()
    ]

    conditions = sorted(
        eligible["production_condition"]
        .dropna()
        .astype(str).str.strip()
        .unique()
    )

    condition = get_choice(
        "Enter production condition: ",
        conditions
    )

    exact = eligible[
        eligible["production_condition"].astype(str).str.strip().str.lower()
        == condition.lower()
    ]

    if len(exact) != 1:
        raise ValueError(
            "Could not identify exactly one eligible crop reference."
        )

    crop_data = exact.iloc[0]

    area = get_number(
        "Enter land area in acres: ",
        minimum=0
    )

    return crop, season, condition, area, crop_data



# =====================================================
# 6. MACHINE LEARNING PREDICTIONS
# =====================================================

def get_ml_predictions(
    crop,
    ml_data,
    mapping,
    model,
    preprocessor
):

    print("\n" + "=" * 65)
    print("MACHINE LEARNING INPUTS")
    print("=" * 65)

    temperature = get_number("Enter temperature: ")
    humidity = get_number("Enter humidity: ")
    moisture = get_number("Enter moisture: ")

    soil_types = sorted(
        ml_data["Soil_Type"].dropna().unique()
    )

    soil_type = get_choice(
        "Enter soil type: ",
        soil_types
    )

    # Crop is passed from the main crop selection.
    # The user cannot accidentally select a different crop here.

    print("\nSelected crop for ML prediction:", crop)

    nitrogen = get_number("Enter Nitrogen value: ")
    potassium = get_number("Enter Potassium value: ")
    phosphorus = get_number("Enter Phosphorous value: ")

    user_data = pd.DataFrame([{

        "Temparature": temperature,
        "Humidity": humidity,
        "Moisture": moisture,
        "Soil_Type": soil_type,
        "Crop_Type": crop,
        "Nitrogen": nitrogen,
        "Potassium": potassium,
        "Phosphorous": phosphorus

    }])

    encoded_data = preprocessor.transform(user_data)

    scores = model.predict_proba(encoded_data)[0]

    fertilizer_names = model.classes_

    ranked_indices = scores.argsort()[::-1][:3]

    predictions = []

    for rank, index in enumerate(ranked_indices, start=1):

        fertilizer = str(fertilizer_names[index]).strip()

        match = mapping[
            mapping["ml_fertilizer_label"].astype(str).str.strip()
            == fertilizer
        ]

        if not match.empty:

            map_row = match.iloc[0]

            product = map_row["composition_product"]
            status = map_row["status"]
            notes = map_row["notes"]

            product = (
                "Not mapped" if pd.isna(product) else product
            )

            status = (
                "Unverified" if pd.isna(status) else status
            )

            notes = (
                "No additional information"
                if pd.isna(notes) else notes
            )

        else:

            product = "Not mapped"
            status = "Unmapped"
            notes = "No mapping available"

        predictions.append({

            "rank": rank,
            "crop_category": crop,
            "ml_fertilizer_label": fertilizer,

            "model_score_percent": round(
                float(scores[index]) * 100, 2
            ),

            "composition_product": product,
            "mapping_status": status,
            "mapping_notes": notes

        })

    return pd.DataFrame(predictions), user_data


# =====================================================
# 7. FERTILIZER COMPOSITION
# =====================================================

def load_composition(composition):

    composition = composition.copy()

    composition["fertilizer_name"] = (
        composition["fertilizer_name"].astype(str).str.strip()
    )

    composition = composition.set_index("fertilizer_name")

    return composition


def verify_composition(composition):

    expected = {

        "DAP": [18, 46, 0],
        "SSP": [0, 16, 0],
        "TSP": [0, 46, 0],
        "Urea": [46, 0, 0],
        "MOP": [0, 0, 60]

    }

    for product, grades in expected.items():

        if product not in composition.index:

            raise ValueError(
                f"Missing fertilizer composition: {product}"
            )

        actual = composition.loc[
            product,
            ["N_percent", "P2O5_percent", "K2O_percent"]
        ].astype(float).tolist()

        if actual != grades:

            raise ValueError(
                f"Fertilizer grade mismatch for {product}. "
                f"Expected {grades}, found {actual}"
            )


# =====================================================
# 8. CALCULATE FERTILIZER COMBINATIONS
# =====================================================

def calculate_combination(
    name,
    phosphorus_source,
    crop_data,
    area,
    composition
):

    area_hectares = area / ACRES_PER_HECTARE

    total_n = float(crop_data["N_kg_ha"]) * area_hectares
    total_p = float(crop_data["P2O5_kg_ha"]) * area_hectares
    total_k = float(crop_data["K2O_kg_ha"]) * area_hectares

    p_grade = float(
        composition.loc[phosphorus_source, "P2O5_percent"]
    )

    p_n_grade = float(
        composition.loc[phosphorus_source, "N_percent"]
    )

    p_s_grade = float(
        composition.loc[phosphorus_source, "S_percent"]
    )

    urea_grade = float(
        composition.loc["Urea", "N_percent"]
    )

    mop_grade = float(
        composition.loc["MOP", "K2O_percent"]
    )

    phosphorus_quantity = total_p * 100 / p_grade

    nitrogen_from_phosphorus = (
        phosphorus_quantity * p_n_grade / 100
    )

    remaining_n = max(
        0,
        total_n - nitrogen_from_phosphorus
    )

    urea_quantity = remaining_n * 100 / urea_grade

    mop_quantity = total_k * 100 / mop_grade

    actual_n = (
        nitrogen_from_phosphorus
        + urea_quantity * urea_grade / 100
    )

    actual_p = phosphorus_quantity * p_grade / 100

    actual_k = mop_quantity * mop_grade / 100

    actual_s = phosphorus_quantity * p_s_grade / 100

    return {

        "crop_category": crop_data["crop_category"],
        "representative_crop": crop_data["representative_crop"],
        "season": crop_data["season"],
        "production_condition": crop_data["production_condition"],
        "region": crop_data["region"],
        "source": crop_data["source"],
        "reference_status": crop_data["status"],

        "area_acres": area,
        "area_hectares": area_hectares,

        "combination": name,
        "phosphorus_fertilizer": phosphorus_source,

        "phosphorus_fertilizer_kg": phosphorus_quantity,
        "urea_kg": urea_quantity,
        "mop_kg": mop_quantity,

        "total_fertilizer_kg": (
            phosphorus_quantity + urea_quantity + mop_quantity
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


def calculate_all_combinations(
    crop_data,
    area,
    composition
):

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
            crop_data,
            area,
            composition
        )

        results.append(result)

    return pd.DataFrame(results)


# =====================================================
# 9. CALCULATE FERTILIZER COSTS
# =====================================================

def calculate_costs(quantity, prices):

    prices = prices.copy()

    prices["fertilizer_name"] = (
        prices["fertilizer_name"].astype(str).str.strip()
    )

    prices["price_per_kg_inr"] = pd.to_numeric(
        prices["price_per_kg_inr"],
        errors="coerce"
    )

    prices["status"] = (
        prices["status"].astype(str).str.strip().str.lower()
    )

    results = []

    for _, row in quantity.iterrows():

        products = [

            (
                row["phosphorus_fertilizer"],
                row["phosphorus_fertilizer_kg"]
            ),

            ("Urea", row["urea_kg"]),
            ("MOP", row["mop_kg"])

        ]

        individual_costs = {}
        statuses = {}

        for product, amount in products:

            match = prices[
                prices["fertilizer_name"].str.lower()
                == product.lower()
            ]

            if match.empty:

                individual_costs[product] = None
                statuses[product] = "Price not found"
                continue

            price_row = match.iloc[0]

            price = price_row["price_per_kg_inr"]
            status = price_row["status"]

            if pd.isna(price) or price <= 0:

                individual_costs[product] = None
                statuses[product] = "Price missing or invalid"

            elif status != "verified":

                individual_costs[product] = None
                statuses[product] = "Price not verified"

            else:

                individual_costs[product] = (
                    float(amount) * float(price)
                )

                statuses[product] = "Verified"

        all_verified = all(
            value == "Verified" for value in statuses.values()
        )

        if all_verified:

            total_cost = sum(individual_costs.values())

            cost_per_acre = (
                total_cost / float(row["area_acres"])
            )

        else:

            total_cost = None
            cost_per_acre = None

        results.append({

            "combination": row["combination"],

            "phosphorus_fertilizer_cost_inr":
                individual_costs.get(row["phosphorus_fertilizer"]),

            "urea_cost_inr": individual_costs.get("Urea"),

            "mop_cost_inr": individual_costs.get("MOP"),

            "total_cost_inr": total_cost,

            "cost_per_acre_inr": cost_per_acre,

            "price_verification": (
                "All prices verified"
                if all_verified
                else "Incomplete - check fertilizer prices"
            ),

            "phosphorus_price_status":
                statuses.get(row["phosphorus_fertilizer"]),

            "urea_price_status": statuses.get("Urea"),

            "mop_price_status": statuses.get("MOP")

        })

    return pd.DataFrame(results)


# =====================================================
# 10. GENERATE FERTILIZER EXPLANATIONS
# =====================================================

def explain_combination(row, composition):

    fertilizers = [

        (
            row["phosphorus_fertilizer"],
            row["phosphorus_fertilizer_kg"]
        ),

        ("Urea", row["urea_kg"]),
        ("MOP", row["mop_kg"])

    ]

    lines = []

    lines.append("=" * 65)
    lines.append("FERTILIZER RECOMMENDATION EXPLANATION")
    lines.append("=" * 65)

    lines.append(f"Crop: {row['representative_crop']}")
    lines.append(f"Season: {row['season']}")
    lines.append(f"Production condition: {row['production_condition']}")
    lines.append(f"Area: {row['area_acres']:.2f} acres")
    lines.append(f"Combination: {row['combination']}")

    lines.append("\nFERTILIZER CONTRIBUTIONS")

    total_n = 0
    total_p = 0
    total_k = 0
    total_s = 0

    for name, amount in fertilizers:

        fertilizer = composition.loc[name]

        n = amount * float(fertilizer["N_percent"]) / 100
        p = amount * float(fertilizer["P2O5_percent"]) / 100
        k = amount * float(fertilizer["K2O_percent"]) / 100
        s = amount * float(fertilizer["S_percent"]) / 100

        total_n += n
        total_p += p
        total_k += k
        total_s += s

        lines.append(f"\n{name}: {amount:.2f} kg")
        lines.append(f"  Nitrogen: {n:.2f} kg")
        lines.append(f"  P2O5: {p:.2f} kg")
        lines.append(f"  K2O: {k:.2f} kg")
        lines.append(f"  Sulphur: {s:.2f} kg")

    lines.append("\nNUTRIENT REQUIREMENT AND SUPPLY")

    lines.append(
        f"Nitrogen: {row['nitrogen_required_kg']:.2f} kg required, "
        f"{total_n:.2f} kg supplied"
    )

    lines.append(
        f"P2O5: {row['phosphorus_required_kg']:.2f} kg required, "
        f"{total_p:.2f} kg supplied"
    )

    lines.append(
        f"K2O: {row['potassium_required_kg']:.2f} kg required, "
        f"{total_k:.2f} kg supplied"
    )

    lines.append(
        f"Additional sulphur supplied: {total_s:.2f} kg"
    )

    lines.append("\nWHY THESE FERTILIZERS ARE INCLUDED")

    lines.append(
        f"{row['phosphorus_fertilizer']} supplies phosphorus "
        "and may also contribute nitrogen or sulphur depending "
        "on its composition."
    )

    lines.append("Urea supplies additional nitrogen.")
    lines.append("MOP supplies potassium.")

    lines.append("\nIMPORTANT LIMITATIONS")

    lines.append(
        "This is a baseline nutrient-based mathematical estimate."
    )

    lines.append(
        "Soil-test N, P and K have not been deducted because "
        "their units and laboratory methods are not confirmed."
    )

    lines.append(
        "Nutrient-use efficiency, application timing, split doses "
        "and crop-specific additional nutrient requirements "
        "are not included."
    )

    lines.append(
        "The three combinations are mathematical alternatives, "
        "not automatically interchangeable agronomic prescriptions."
    )

    lines.append(
        "Consult a local agricultural expert before field application."
    )

    lines.append("=" * 65)

    return "\n".join(lines)


# =====================================================
# 11. DISPLAY SOIL INFORMATION
# =====================================================

def display_soil_information(soil):

    print("\n" + "=" * 65)
    print("SOIL SAMPLE ANALYSIS")
    print("=" * 65)

    columns = [
        "Sample",
        "pH",
        "EC",
        "OC",
        "N",
        "P",
        "K",
        "OC_Status",
        "Nitrogen_Status",
        "Phosphorus_Status",
        "Potassium_Status",
        "pH_Status",
        "EC_Status",
        "Soil_Health_Score",
        "Soil_Health_Category"
    ]

    for column in columns:

        if column in soil.index:

            print(f"{column}: {soil[column]}")


# =====================================================
# 12. DISPLAY ML PREDICTIONS
# =====================================================

def display_ml_predictions(predictions):

    print("\n" + "=" * 65)
    print("TOP 3 MACHINE LEARNING PREDICTIONS")
    print("=" * 65)

    for _, row in predictions.iterrows():

        print("\nRank:", row["rank"])

        print(
            "Fertilizer:",
            row["ml_fertilizer_label"]
        )

        print(
            "Model ranking score:",
            row["model_score_percent"],
            "%"
        )

        print(
            "Composition product:",
            row["composition_product"]
        )

        print(
            "Mapping status:",
            row["mapping_status"]
        )

        print("Notes:", row["mapping_notes"])

        if str(row["mapping_status"]).lower() != "verified":

            print("CAUTION: Product mapping needs confirmation.")

    print("\nModel scores are ranking scores,")
    print("not guaranteed probabilities of fertilizer effectiveness.")


# =====================================================
# 13. DISPLAY FERTILIZER COMPARISON
# =====================================================


def display_comparison(quantity, costs):

    report = pd.merge(
        quantity,
        costs,
        on="combination",
        how="left",
        suffixes=("", "_cost")
    )

    # Keep the original cost verification status.
    # Do not combine it with another status column.
    if "price_verification_cost" in report.columns:
        report["price_verification"] = (
            report["price_verification_cost"]
        )

    report["price_verification"] = (
        report["price_verification"]
        .fillna("Incomplete - check fertilizer prices")
        .astype(str)
        .str.strip()
        .str.replace(
            "All prices verifiedVerified",
            "All prices verified",
            regex=False
        )
    )

    print("\n" + "=" * 65)
    print("CROP-SPECIFIC FERTILIZER QUANTITY AND COST")
    print("=" * 65)

    for _, row in report.iterrows():

        print("\n" + row["combination"])
        print("-" * 55)

        print("Crop:", row["representative_crop"])
        print("Season:", row["season"])
        print("Area:", round(row["area_acres"], 2), "acres")

        print(
            row["phosphorus_fertilizer"] + ":",
            round(row["phosphorus_fertilizer_kg"], 2),
            "kg"
        )

        print("Urea:", round(row["urea_kg"], 2), "kg")
        print("MOP:", round(row["mop_kg"], 2), "kg")

        print(
            "Total fertilizer:",
            round(row["total_fertilizer_kg"], 2),
            "kg"
        )

        print(
            "N supplied:",
            round(row["nitrogen_supplied_kg"], 2),
            "kg"
        )

        print(
            "P2O5 supplied:",
            round(row["phosphorus_supplied_kg"], 2),
            "kg"
        )

        print(
            "K2O supplied:",
            round(row["potassium_supplied_kg"], 2),
            "kg"
        )

        print(
            "Sulphur supplied:",
            round(row["sulphur_supplied_kg"], 2),
            "kg"
        )

        if pd.notna(row["total_cost_inr"]):

            print(
                "Estimated total cost: Rs.",
                round(row["total_cost_inr"], 2)
            )

            print(
                "Estimated cost per acre: Rs.",
                round(row["cost_per_acre_inr"], 2)
            )

        else:

            print("Estimated cost: Not available")
            print("Reason: One or more prices are unverified.")

        print("Price status:", row["price_verification"])

    return report



# =====================================================
# 14. SAVE ALL REPORTS
# =====================================================

def save_all_reports(
    soil_sample,
    crop,
    ml_input,
    predictions,
    quantity,
    costs,
    explanations,
    integrated
):

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(QUANTITY_DIR, exist_ok=True)
    os.makedirs(COST_DIR, exist_ok=True)
    os.makedirs(EXPLANATION_DIR, exist_ok=True)

    sample_id = str(
        soil_sample["Sample"]
    ).replace(" ", "_")

    # Quantity report
    quantity_path = os.path.join(
        QUANTITY_DIR,
        "fertilizer_combination_comparison.csv"
    )

    quantity.to_csv(quantity_path, index=False)

    # Cost report
    cost_path = os.path.join(
        COST_DIR,
        "fertilizer_cost_comparison.csv"
    )

    costs.to_csv(cost_path, index=False)

    # Explanation CSV
    explanation_rows = []

    for _, row in quantity.iterrows():

        explanation_rows.append({

            "crop": row["representative_crop"],
            "season": row["season"],
            "combination": row["combination"],
            "area_acres": row["area_acres"],

            "nitrogen_required_kg": row["nitrogen_required_kg"],
            "nitrogen_supplied_kg": row["nitrogen_supplied_kg"],

            "phosphorus_required_kg": row["phosphorus_required_kg"],
            "phosphorus_supplied_kg": row["phosphorus_supplied_kg"],

            "potassium_required_kg": row["potassium_required_kg"],
            "potassium_supplied_kg": row["potassium_supplied_kg"],

            "sulphur_supplied_kg": row["sulphur_supplied_kg"]

        })

    explanation_path = os.path.join(
        EXPLANATION_DIR,
        "fertilizer_explanation_report.csv"
    )

    pd.DataFrame(explanation_rows).to_csv(
        explanation_path,
        index=False
    )

    # Explanation text
    text_path = os.path.join(
        EXPLANATION_DIR,
        "fertilizer_explanation.txt"
    )

    with open(text_path, "w", encoding="utf-8") as file:

        for explanation in explanations:

            file.write(explanation)
            file.write("\n\n")

    # Integrated farmer report
    integrated_path = os.path.join(
        OUTPUT_DIR,
        f"integrated_report_{sample_id}.csv"
    )

    integrated.to_csv(integrated_path, index=False)

    # Soil details
    soil_path = os.path.join(
        OUTPUT_DIR,
        f"soil_details_{sample_id}.csv"
    )

    pd.DataFrame([soil_sample]).to_csv(
        soil_path,
        index=False
    )

    # ML predictions
    ml_path = os.path.join(
        OUTPUT_DIR,
        f"ml_predictions_{sample_id}.csv"
    )

    predictions.to_csv(ml_path, index=False)

    # ML input details
    input_path = os.path.join(
        OUTPUT_DIR,
        f"ml_input_{sample_id}.csv"
    )

    ml_input.to_csv(input_path, index=False)

    print("\n" + "=" * 65)
    print("ALL REPORTS SAVED SUCCESSFULLY")
    print("=" * 65)

    print("Quantity report:", quantity_path)
    print("Cost report:", cost_path)
    print("Explanation CSV:", explanation_path)
    print("Explanation text:", text_path)
    print("Integrated report:", integrated_path)
    print("Soil details:", soil_path)
    print("ML predictions:", ml_path)
    print("ML input:", input_path)


# =====================================================
# 15. MAIN PROGRAM
# =====================================================

def main():

    print("\n" + "=" * 65)
    print("SMART FERTILIZER RECOMMENDATION SYSTEM")
    print("DYNAMIC INTEGRATED FARMER REPORT")
    print("=" * 65)

    try:

        (
            soil,
            crops,
            composition_data,
            prices,
            ml_data,
            mapping,
            model,
            preprocessor
        ) = load_project_data()

        print("\nProject data loaded successfully.")

        # Soil sample
        selected_soil = select_soil_sample(soil)

        display_soil_information(selected_soil)

        # One crop selection shared by ML and agronomic calculations
        crop, season, condition, area, crop_data = (
            select_crop_details(crops, ml_data)
        )

        print("\nSelected crop:", crop)
        print("Representative crop:", crop_data["representative_crop"])
        print("Season:", season)
        print("Production condition:", condition)
        print("Area:", area, "acres")
        print("Crop reference:", crop_data["source"])
        print("Reference status:", crop_data["status"])

        # Composition
        composition = load_composition(composition_data)
        verify_composition(composition)

        # ML predictions
        predictions, ml_input = get_ml_predictions(
            crop,
            ml_data,
            mapping,
            model,
            preprocessor
        )

        # Dynamic crop-specific quantity calculations
        quantity = calculate_all_combinations(
            crop_data,
            area,
            composition
        )

        # Dynamic price calculations
        costs = calculate_costs(
            quantity,
            prices
        )

        # Generate explanations for all combinations
        explanations = []

        for _, row in quantity.iterrows():

            explanations.append(
                explain_combination(row, composition)
            )

        # Merge quantities and costs
        integrated = display_comparison(
            quantity,
            costs
        )

        # Display predictions
        display_ml_predictions(predictions)

        # Display limitations
        print("\n" + "=" * 65)
        print("SOIL ADJUSTMENT AND IMPORTANT LIMITATIONS")
        print("=" * 65)

        print(
            "Adjustment applied:",
            selected_soil.get(
                "Fertilizer_Quantity_Adjustment",
                "Not available"
            )
        )

        print(
            "Reason:",
            selected_soil.get(
                "Adjustment_Reason",
                "Not available"
            )
        )

        print(
            "Soil-test N, P and K units and laboratory methods "
            "are not confirmed."
        )

        print(
            "Therefore, soil-test nutrient values have not been "
            "deducted from crop nutrient requirements."
        )

        print(
            "Cost references may not represent current local "
            "supplier quotations."
        )

        print(
            "The three fertilizer combinations are mathematical "
            "nutrient-supply alternatives, not automatically "
            "interchangeable field prescriptions."
        )

        print(
            "Consult a local agricultural expert before actual "
            "fertilizer application."
        )

        # Save everything
        save_all_reports(
            selected_soil,
            crop,
            ml_input,
            predictions,
            quantity,
            costs,
            explanations,
            integrated
        )

        print("\n" + "=" * 65)
        print("INTEGRATED RECOMMENDATION COMPLETED SUCCESSFULLY!")
        print("=" * 65)

    except FileNotFoundError as error:

        print("\nFILE ERROR:", error)

    except Exception as error:

        print("\nERROR:", error)


# =====================================================
# 16. PROGRAM EXECUTION
# =====================================================

if __name__ == "__main__":
    main()
