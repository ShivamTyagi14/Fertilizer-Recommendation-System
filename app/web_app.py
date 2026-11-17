
import os
import sys
import math
from pathlib import Path

import pandas as pd
from flask import Flask, render_template, request

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from integrated_recommendation import load_project_data

app = Flask(__name__)

project_data = None
data_error = None

try:
    project_data = load_project_data()
    print("Project data loaded successfully.")
except Exception as error:
    data_error = str(error)
    print("Project data loading error:", data_error)


# -----------------------------------------------------
# 1. GET FORM CHOICES
# -----------------------------------------------------

def get_form_choices():

    (
        soil, crops, composition, prices,
        ml_data, mapping, model, preprocessor
    ) = project_data

    crop_names = sorted(
        ml_data["Crop_Type"].dropna().astype(str)
        .str.strip().unique().tolist()
    )

    soil_types = sorted(
        ml_data["Soil_Type"].dropna().astype(str)
        .str.strip().unique().tolist()
    )

    return crop_names, soil_types


# -----------------------------------------------------
# 2. GET QUANTITY REFERENCE CHOICES
# -----------------------------------------------------

def get_quantity_choices():

    (
        soil, crops, composition, prices,
        ml_data, mapping, model, preprocessor
    ) = project_data

    eligible = crops[
        crops["status"].astype(str).str.strip().str.lower()
        .isin(["verified", "regional reference"])
    ].copy()

    eligible = eligible.dropna(
        subset=["N_kg_ha", "P2O5_kg_ha", "K2O_kg_ha"]
    )

    seasons = sorted(
        eligible["season"].dropna().astype(str)
        .str.strip().unique().tolist()
    )

    conditions = sorted(
        eligible["production_condition"].dropna().astype(str)
        .str.strip().unique().tolist()
    )

    return seasons, conditions


# -----------------------------------------------------
# 3. SOIL HEALTH CLASSIFICATION FUNCTIONS
# -----------------------------------------------------

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


# -----------------------------------------------------
# 4. SOIL HEALTH SCORING FUNCTIONS
# -----------------------------------------------------

def nutrient_score(status):

    if status == "Low":
        return 0
    elif status == "Medium":
        return 50
    elif status == "High":
        return 100

    return 0


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


def classify_soil_health(score):

    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Moderate"
    else:
        return "Poor"


# -----------------------------------------------------
# 5. CALCULATE COMPLETE SOIL HEALTH REPORT
# -----------------------------------------------------

def calculate_soil_health(form_data):

    field_names = {
        "pH": "soil_ph",
        "EC": "soil_ec",
        "OC": "soil_oc",
        "Nitrogen": "soil_nitrogen",
        "Phosphorus": "soil_phosphorus",
        "Potassium": "soil_potassium"
    }

    values = {}

    for parameter, field in field_names.items():

        raw_value = form_data.get(field, "").strip()

        if raw_value == "":
            return None

        try:
            value = float(raw_value)
        except (ValueError, TypeError):
            raise ValueError(
                parameter + " must be a valid number."
            )

        if not math.isfinite(value):
            raise ValueError(
                parameter + " must be a valid finite number."
            )

        if value < 0:
            raise ValueError(
                parameter + " cannot be negative."
            )

        values[parameter] = value

    if values["pH"] > 14:
        raise ValueError("Soil pH must be between 0 and 14.")

    statuses = {
        "OC_Status": classify_organic_carbon(values["OC"]),
        "Nitrogen_Status": classify_nitrogen(values["Nitrogen"]),
        "Phosphorus_Status": classify_phosphorus(values["Phosphorus"]),
        "Potassium_Status": classify_potassium(values["Potassium"]),
        "pH_Status": classify_ph(values["pH"]),
        "EC_Status": classify_ec(values["EC"])
    }

    scores = {
        "OC_Score": nutrient_score(statuses["OC_Status"]),
        "Nitrogen_Score": nutrient_score(
            statuses["Nitrogen_Status"]
        ),
        "Phosphorus_Score": nutrient_score(
            statuses["Phosphorus_Status"]
        ),
        "Potassium_Score": nutrient_score(
            statuses["Potassium_Status"]
        ),
        "pH_Score": ph_score(statuses["pH_Status"]),
        "EC_Score": ec_score(statuses["EC_Status"])
    }

    overall_score = round(
        sum(scores.values()) / len(scores), 2
    )

    category = classify_soil_health(overall_score)

    suggestions = []

    if statuses["OC_Status"] == "Low":
        suggestions.append(
            "Organic carbon is low. Consider suitable organic "
            "matter management, such as compost or well-decomposed "
            "farmyard manure."
        )

    if statuses["Nitrogen_Status"] == "Low":
        suggestions.append(
            "Nitrogen is low according to the project's "
            "classification threshold."
        )

    if statuses["Phosphorus_Status"] == "Low":
        suggestions.append(
            "Phosphorus is low according to the project's "
            "classification threshold."
        )

    if statuses["Potassium_Status"] == "Low":
        suggestions.append(
            "Potassium is low according to the project's "
            "classification threshold."
        )

    if statuses["pH_Status"] == "Acidic":
        suggestions.append(
            "Soil is acidic. Consider a laboratory-based "
            "liming recommendation."
        )

    elif statuses["pH_Status"] == "Tending to become alkaline":
        suggestions.append(
            "Soil pH is tending towards alkaline conditions. "
            "Monitor pH and follow a soil-test-based management plan."
        )

    elif statuses["pH_Status"] == "Alkaline":
        suggestions.append(
            "Soil is alkaline. Obtain a laboratory-based "
            "amendment recommendation."
        )

    if statuses["EC_Status"] != "Normal":
        suggestions.append(
            "Electrical conductivity indicates a possible "
            "salinity concern. Check irrigation water and "
            "soil drainage."
        )

    if not suggestions:
        suggestions.append(
            "No low nutrient classification or pH/EC warning "
            "was identified by the project's adopted rules."
        )

    return {
        "values": values,
        "statuses": statuses,
        "scores": scores,
        "soil_health_score": overall_score,
        "soil_health_category": category,
        "suggestions": suggestions
    }


# -----------------------------------------------------
# 6. CALCULATE PREDICTED FERTILIZER QUANTITY
# -----------------------------------------------------

def calculate_predicted_fertilizer(
    predicted_fertilizer,
    crop_data,
    mapping,
    composition,
    prices,
    area=1.0
):

    mapping_rows = mapping[
        mapping["ml_fertilizer_label"].astype(str).str.strip()
        == str(predicted_fertilizer).strip()
    ]

    if len(mapping_rows) != 1:
        raise ValueError("No unique fertilizer mapping found.")

    mapping_row = mapping_rows.iloc[0]

    if str(mapping_row["status"]).strip().lower() != "verified":
        raise ValueError("The predicted fertilizer mapping is not verified.")

    product_name = str(mapping_row["composition_product"]).strip()

    if not product_name or product_name.lower() == "nan":
        raise ValueError("No verified composition product is mapped.")

    if product_name not in composition.index:
        raise ValueError("Composition not found for " + product_name)

    product = composition.loc[product_name]

    if isinstance(product, pd.DataFrame):
        raise ValueError("Duplicate fertilizer composition records found.")

    if str(product["status"]).strip().lower() != "verified":
        raise ValueError("The fertilizer composition is not verified.")

    acre_factor = 0.404686

    required = {
        "N": float(crop_data["N_kg_ha"]) * acre_factor * area,
        "P2O5": float(crop_data["P2O5_kg_ha"]) * acre_factor * area,
        "K2O": float(crop_data["K2O_kg_ha"]) * acre_factor * area
    }

    percentages = {
        "N": float(product["N_percent"]),
        "P2O5": float(product["P2O5_percent"]),
        "K2O": float(product["K2O_percent"])
    }

    if any(value < 0 or value > 100 for value in percentages.values()):
        raise ValueError("Invalid fertilizer composition percentages.")

    possible_quantities = {}

    for nutrient, percentage in percentages.items():

        if percentage > 0 and required[nutrient] > 0:

            possible_quantities[nutrient] = (
                required[nutrient] * 100 / percentage
            )

    if not possible_quantities:
        raise ValueError("The fertilizer has no usable NPK composition.")

    limiting_nutrient = min(
        possible_quantities,
        key=possible_quantities.get
    )

    fertilizer_quantity = possible_quantities[limiting_nutrient]

    nutrient_results = {}

    for nutrient in ["N", "P2O5", "K2O"]:

        supplied = fertilizer_quantity * percentages[nutrient] / 100

        deficit = max(0, required[nutrient] - supplied)
        excess = max(0, supplied - required[nutrient])

        nutrient_results[nutrient] = {
            "required_kg": round(required[nutrient], 2),
            "supplied_kg": round(supplied, 2),
            "deficit_kg": round(deficit, 2),
            "excess_kg": round(excess, 2)
        }

    price_rows = prices[
        (
            prices["fertilizer_name"].astype(str).str.strip()
            == product_name
        )
        &
        (
            prices["status"].astype(str).str.strip().str.lower()
            == "verified"
        )
    ]

    price_per_kg = None
    estimated_cost = None

    if len(price_rows) == 1:

        raw_price = pd.to_numeric(
            price_rows.iloc[0]["price_per_kg_inr"],
            errors="coerce"
        )

        if pd.notna(raw_price) and raw_price > 0:

            price_per_kg = float(raw_price)
            estimated_cost = fertilizer_quantity * price_per_kg

    return {
        "ml_fertilizer": predicted_fertilizer,
        "product_name": product_name,
        "grade": str(product["grade"]),
        "area_acres": area,
        "quantity_kg": round(fertilizer_quantity, 2),
        "limiting_nutrient": limiting_nutrient,
        "nutrients": nutrient_results,
        "price_per_kg": (
            round(price_per_kg, 2)
            if price_per_kg is not None else None
        ),
        "estimated_cost": (
            round(estimated_cost, 2)
            if estimated_cost is not None else None
        )
    }


# -----------------------------------------------------
# 7. DASHBOARD
# -----------------------------------------------------

@app.route("/")
def dashboard():

    if project_data is None:

        return render_template(
            "index.html",
            data_loaded=False,
            error=data_error
        )

    (
        soil, crops, composition, prices,
        ml_data, mapping, model, preprocessor
    ) = project_data

    raw_soil = pd.read_csv(
        PROJECT_ROOT / "data" / "raw" / "agrinet_soil.csv"
    )

    crop_names = sorted(
        crops["crop_category"].dropna().astype(str)
        .str.strip().unique().tolist()
    )

    return render_template(
        "index.html",
        data_loaded=True,
        soil_count=len(raw_soil),
        crop_count=len(crop_names),
        fertilizer_count=len(model.classes_),
        composition_count=len(composition),
        price_count=len(prices),
        crop_names=crop_names,
        sample_names=raw_soil["Sample"].dropna()
        .astype(str).tolist()[:10]
    )


# -----------------------------------------------------
# 8. INDEPENDENT FERTILIZER RECOMMENDATION
# -----------------------------------------------------

@app.route("/recommend", methods=["GET", "POST"])
def recommend_form():

    if project_data is None:
        return "Project data could not be loaded: " + str(data_error)

    (
        soil, crops, composition, prices,
        ml_data, mapping, model, preprocessor
    ) = project_data

    crop_names, soil_types = get_form_choices()
    seasons, conditions = get_quantity_choices()

    if request.method == "GET":

        return render_template(
            "recommend.html",
            crop_names=crop_names,
            soil_types=soil_types,
            seasons=seasons,
            conditions=conditions
        )

    try:

        # A. COLLECT ML INPUTS

        input_data = {
            "Temparature": float(request.form["temperature"]),
            "Humidity": float(request.form["humidity"]),
            "Moisture": float(request.form["moisture"]),
            "Soil_Type": request.form["soil_type"],
            "Crop_Type": request.form["crop_type"],
            "Nitrogen": float(request.form["nitrogen"]),
            "Potassium": float(request.form["potassium"]),
            "Phosphorous": float(request.form["phosphorus"])
        }

        # B. VALIDATE ML INPUTS

        for feature, value in input_data.items():

            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(feature + " must be a valid number.")

        if not 0 <= input_data["Humidity"] <= 100:
            raise ValueError("Humidity must be between 0 and 100.")

        if not 0 <= input_data["Temparature"] <= 60:
            raise ValueError("Temperature must be between 0 and 60 °C.")

        for feature in [
            "Nitrogen", "Potassium", "Phosphorous", "Moisture"
        ]:

            if input_data[feature] < 0:
                raise ValueError(feature + " cannot be negative.")

        if input_data["Crop_Type"] not in crop_names:
            raise ValueError("Please select a valid crop.")

        if input_data["Soil_Type"] not in soil_types:
            raise ValueError("Please select a valid soil type.")

        # C. MACHINE LEARNING PREDICTION

        input_df = pd.DataFrame([input_data])

        processed_input = preprocessor.transform(input_df)

        # Get probability of every fertilizer class
        probabilities = model.predict_proba(processed_input)[0]
        classes = model.classes_

        # Check that the model supports probability prediction
        if len(probabilities) != len(classes):
            raise ValueError(
                "Model probability output does not match its classes."
            )

        # Get indexes of the three highest probabilities
        top_indices = probabilities.argsort()[::-1][:3]

        # Keep all three predictions in this list
        predictions = []

        for index in top_indices:

            predictions.append({
                "fertilizer": str(classes[index]),
                "score": round(float(probabilities[index]) * 100, 2)
            })

        # First-ranked fertilizer is the primary recommendation
        predicted_fertilizer = predictions[0]["fertilizer"]

        prediction_score = predictions[0]["score"]

        # DEBUG: Check predictions in VS Code terminal
        print("\n===== TOP 3 FERTILIZER PREDICTIONS =====")

        for item in predictions:
            print(
                item["fertilizer"],
                "-",
                item["score"],
                "%"
            )

        print("Total predictions:", len(predictions))

        # D. QUANTITY AND COST

        quantity_records = []
        cost_records = []
        explanations = []

        quantity_message = None
        quantity_available = False

        area = 1.0

        selected_season = request.form.get("season", "").strip()

        selected_condition = request.form.get(
            "production_condition", ""
        ).strip()

        selected_crop = input_data["Crop_Type"]

        try:

            eligible = crops[
                (
                    crops["crop_category"].astype(str).str.strip().str.lower()
                    == selected_crop.lower()
                )
                &
                (
                    crops["status"].astype(str).str.strip().str.lower()
                    .isin(["verified", "regional reference"])
                )
            ].copy()

            eligible = eligible.dropna(
                subset=["N_kg_ha", "P2O5_kg_ha", "K2O_kg_ha"]
            )

            if eligible.empty:

                quantity_message = (
                    "Fertilizer predicted successfully. "
                    "Quantity and cost are unavailable because no "
                    "complete nutrient reference exists for this crop."
                )

            elif not selected_season or not selected_condition:

                quantity_message = (
                    "Fertilizer predicted successfully. "
                    "Select season and production condition to calculate "
                    "quantity and cost."
                )

            else:

                season_values = (
                    eligible["season"].astype(str).str.strip().str.lower()
                )

                condition_values = (
                    eligible["production_condition"]
                    .astype(str).str.strip().str.lower()
                )

                season_match = (
                    (season_values == selected_season.lower())
                    | (season_values == "not specified")
                )

                condition_match = (
                    (condition_values == selected_condition.lower())
                    | (condition_values == "not specified")
                )

                matching_crop = eligible[
                    season_match & condition_match
                ]

                if matching_crop.empty:

                    quantity_message = (
                        "Fertilizer predicted successfully. "
                        "No matching nutrient reference was found for "
                        "this season and production condition. "
                        "Quantity and cost are unavailable."
                    )

                else:

                    matching_crop = matching_crop.copy()

                    matching_crop["_specificity"] = (
                        (
                            season_values.loc[matching_crop.index]
                            != "not specified"
                        ).astype(int)
                        +
                        (
                            condition_values.loc[matching_crop.index]
                            != "not specified"
                        ).astype(int)
                    )

                    crop_data = matching_crop.sort_values(
                        "_specificity", ascending=False
                    ).iloc[0]

                    result = calculate_predicted_fertilizer(
                        predicted_fertilizer,
                        crop_data,
                        mapping,
                        composition,
                        prices,
                        area
                    )

                    quantity_records = [result]
                    quantity_available = True

                    if result["estimated_cost"] is None:

                        quantity_message = (
                            "Quantity calculated successfully, but a "
                            "verified price is not available for this product."
                        )

        except (ValueError, TypeError, KeyError, IndexError) as error:

            quantity_message = (
                "Fertilizer predicted successfully. "
                "Quantity or cost could not be calculated: "
                + str(error)
            )

        # E. DISPLAY FERTILIZER RESULT

        return render_template(
            "result.html",
            input_data=input_data,
            predictions=predictions,
            predicted_fertilizer=predicted_fertilizer,
            prediction_score=prediction_score,
            quantity_available=quantity_available,
            quantity_message=quantity_message,
            quantity_records=quantity_records,
            cost_records=cost_records,
            explanations=explanations,
            area=area,
            selected_season=selected_season,
            selected_condition=selected_condition
        )

    except (ValueError, TypeError, KeyError) as error:

        return render_template(
            "recommend.html",
            crop_names=crop_names,
            soil_types=soil_types,
            seasons=seasons,
            conditions=conditions,
            error=str(error)
        )


# -----------------------------------------------------
# 9. INDEPENDENT SOIL HEALTH ANALYSIS PAGE
# -----------------------------------------------------

@app.route("/soil-health", methods=["GET", "POST"])
def soil_health_page():

    if request.method == "POST":
        try:
            soil_health = calculate_soil_health(request.form)

            return render_template(
                "soil_health_result.html",
                soil_health=soil_health
            )

        except Exception as error:
            return render_template(
                "soil_health.html",
                soil_health=None,
                error=str(error)
            )

    return render_template(
        "soil_health.html",
        soil_health=None
    )


# -----------------------------------------------------
# 10. RUN FLASK APPLICATION
# -----------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
