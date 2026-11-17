
import pandas as pd
import os

# ==========================================
# 1. FILE PATHS
# ==========================================

PRICE_FILE = "data/reference/fertilizer_prices.csv"

QUANTITY_FILE = (
    "outputs/fertilizer_quantity/"
    "fertilizer_combination_comparison.csv"
)

OUTPUT_FOLDER = "outputs/fertilizer_cost"
OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "fertilizer_cost_comparison.csv"
)


# ==========================================
# 2. LOAD FERTILIZER PRICES
# ==========================================

def load_fertilizer_prices():

    if not os.path.exists(PRICE_FILE):
        raise FileNotFoundError(
            f"Price file not found: {PRICE_FILE}"
        )

    prices = pd.read_csv(PRICE_FILE)

    required_columns = [
        "fertilizer_name",
        "price_per_kg_inr",
        "source",
        "price_date",
        "status"
    ]

    for column in required_columns:
        if column not in prices.columns:
            raise ValueError(
                f"Missing column in price file: {column}"
            )

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

    return prices


# ==========================================
# 3. LOAD QUANTITY COMPARISON
# ==========================================

def load_quantity_data():

    if not os.path.exists(QUANTITY_FILE):
        raise FileNotFoundError(
            f"Quantity report not found: {QUANTITY_FILE}"
        )

    data = pd.read_csv(QUANTITY_FILE)

    required_columns = [
        "crop_category",
        "representative_crop",
        "season",
        "region",
        "area_acres",
        "combination",
        "phosphorus_fertilizer",
        "phosphorus_fertilizer_kg",
        "urea_kg",
        "mop_kg"
    ]

    for column in required_columns:
        if column not in data.columns:
            raise ValueError(
                f"Missing column in quantity report: {column}"
            )

    return data


# ==========================================
# 4. CALCULATE COST OF ONE FERTILIZER
# ==========================================

def calculate_fertilizer_cost(
    fertilizer_name,
    quantity,
    prices
):

    matching_rows = prices[
        prices["fertilizer_name"].str.lower()
        == str(fertilizer_name).strip().lower()
    ]

    if matching_rows.empty:
        return None, "Price not found"

    price_row = matching_rows.iloc[0]

    price = price_row["price_per_kg_inr"]
    status = price_row["status"]

    if pd.isna(price) or price <= 0:
        return None, "Price missing or invalid"

    if status != "verified":
        return None, "Price not verified"

    cost = float(quantity) * float(price)

    return cost, "Verified"


# ==========================================
# 5. CALCULATE ALL COMBINATION COSTS
# ==========================================

def calculate_all_costs(data, prices):

    results = []

    for _, row in data.iterrows():

        phosphorus_fertilizer = row[
            "phosphorus_fertilizer"
        ]

        phosphorus_quantity = row[
            "phosphorus_fertilizer_kg"
        ]

        urea_quantity = row["urea_kg"]
        mop_quantity = row["mop_kg"]

        # Calculate individual fertilizer costs

        phosphorus_cost, phosphorus_status = (
            calculate_fertilizer_cost(
                phosphorus_fertilizer,
                phosphorus_quantity,
                prices
            )
        )

        urea_cost, urea_status = (
            calculate_fertilizer_cost(
                "Urea",
                urea_quantity,
                prices
            )
        )

        mop_cost, mop_status = (
            calculate_fertilizer_cost(
                "MOP",
                mop_quantity,
                prices
            )
        )

        all_verified = all([
            phosphorus_status == "Verified",
            urea_status == "Verified",
            mop_status == "Verified"
        ])

        if all_verified:

            total_cost = (
                phosphorus_cost
                + urea_cost
                + mop_cost
            )

            area = float(row["area_acres"])

            cost_per_acre = (
                total_cost / area if area > 0 else None
            )

        else:
            total_cost = None
            cost_per_acre = None

        results.append({

            "crop_category": row["crop_category"],
            "representative_crop": row[
                "representative_crop"
            ],
            "season": row["season"],
            "region": row["region"],
            "area_acres": row["area_acres"],

            "combination": row["combination"],

            "phosphorus_fertilizer":
                phosphorus_fertilizer,

            "phosphorus_fertilizer_kg":
                phosphorus_quantity,

            "phosphorus_fertilizer_cost_inr":
                phosphorus_cost,

            "urea_kg": urea_quantity,
            "urea_cost_inr": urea_cost,

            "mop_kg": mop_quantity,
            "mop_cost_inr": mop_cost,

            "total_cost_inr": total_cost,
            "cost_per_acre_inr": cost_per_acre,

            "price_verification": (
                "All prices verified"
                if all_verified
                else "Incomplete - check fertilizer prices"
            ),

            "phosphorus_price_status":
                phosphorus_status,

            "urea_price_status": urea_status,
            "mop_price_status": mop_status
        })

    return pd.DataFrame(results)


# ==========================================
# 6. DISPLAY RESULTS
# ==========================================

def display_results(results):

    print("\n" + "=" * 65)
    print("FERTILIZER COST COMPARISON")
    print("=" * 65)

    for _, row in results.iterrows():

        print("\nCombination:", row["combination"])

        print(
            "Phosphorus fertilizer:",
            row["phosphorus_fertilizer"]
        )

        print(
            "Phosphorus fertilizer cost:",
            row["phosphorus_fertilizer_cost_inr"]
        )

        print("Urea cost:", row["urea_cost_inr"])
        print("MOP cost:", row["mop_cost_inr"])

        if pd.notna(row["total_cost_inr"]):

            print(
                "Total cost: Rs.",
                round(row["total_cost_inr"], 2)
            )

            print(
                "Cost per acre: Rs.",
                round(row["cost_per_acre_inr"], 2)
            )

        else:
            print("Total cost: Not calculated")
            print("Reason: One or more prices are unverified.")

        print(
            "Price status:",
            row["price_verification"]
        )

    # Identify the lowest cost only among complete results

    valid_results = results.dropna(
        subset=["total_cost_inr"]
    )

    print("\n" + "=" * 65)
    print("COST COMPARISON SUMMARY")
    print("=" * 65)

    if not valid_results.empty:

        cheapest = valid_results.loc[
            valid_results["total_cost_inr"].idxmin()
        ]

        print(
            "Lowest estimated cost:",
            cheapest["combination"]
        )

        print(
            "Total cost: Rs.",
            round(cheapest["total_cost_inr"], 2)
        )

        print(
            "Cost per acre: Rs.",
            round(cheapest["cost_per_acre_inr"], 2)
        )

        if len(valid_results) < len(results):
            print(
                "\nNote: Some combinations were excluded "
                "because their prices are unverified."
            )

    else:

        print(
            "No complete cost comparison is possible yet."
        )

        print(
            "Please verify all required fertilizer prices."
        )


# ==========================================
# 7. SAVE COST REPORT
# ==========================================

def save_cost_report(results):

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    results.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 65)
    print("COST REPORT SAVED SUCCESSFULLY")
    print("=" * 65)

    print("File:", OUTPUT_FILE)


# ==========================================
# 8. MAIN PROGRAM
# ==========================================

def main():

    print("=" * 65)
    print("FERTILIZER COST ESTIMATION SYSTEM")
    print("=" * 65)

    prices = load_fertilizer_prices()
    quantity_data = load_quantity_data()

    results = calculate_all_costs(
        quantity_data,
        prices
    )

    display_results(results)

    save_cost_report(results)

    print("\nCOST ESTIMATION COMPLETED!")


# ==========================================
# 9. PROGRAM EXECUTION
# ==========================================

if __name__ == "__main__":
    main()
