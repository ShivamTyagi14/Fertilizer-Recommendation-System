
import pandas as pd
from pathlib import Path

# Load fertilizer composition reference table
file_path = "data/reference/fertilizer_composition.csv"
df = pd.read_csv(file_path)

print("=" * 50)
print("FERTILIZER COMPOSITION VALIDATION")
print("=" * 50)

# Required columns
required_columns = [
    "fertilizer_name",
    "grade",
    "N_percent",
    "P2O5_percent",
    "K2O_percent",
    "S_percent",
    "source",
    "status"
]

# Check 1: Required columns
missing_columns = [
    col for col in required_columns if col not in df.columns
]

if not missing_columns:
    print("PASS: All required columns are present.")
else:
    print("FAIL: Missing columns:", missing_columns)

# Check 2: Missing values
if df.isnull().sum().sum() == 0:
    print("PASS: No missing values.")
else:
    print("FAIL: Missing values found.")

# Check 3: Duplicate fertilizer names
duplicates = df["fertilizer_name"].duplicated().sum()

if duplicates == 0:
    print("PASS: No duplicate fertilizer names.")
else:
    print("FAIL: Duplicate fertilizer names:", duplicates)

# Check 4: Nutrient percentages
nutrient_columns = [
    "N_percent",
    "P2O5_percent",
    "K2O_percent",
    "S_percent"
]

invalid_values = []

for column in nutrient_columns:
    invalid = df[
        (df[column] < 0) | (df[column] > 100)
    ]

    if not invalid.empty:
        invalid_values.extend(invalid["fertilizer_name"].tolist())

if not invalid_values:
    print("PASS: All nutrient percentages are between 0 and 100.")
else:
    print("FAIL: Invalid nutrient percentages:", invalid_values)

# Check 5: Basic known-grade consistency
known_grades = {
    "Urea": [46, 0, 0],
    "DAP": [18, 46, 0],
    "MOP": [0, 0, 60],
    "TSP": [0, 46, 0]
}

grade_errors = []

for fertilizer, expected in known_grades.items():
    matching = df[
        df["fertilizer_name"].str.lower() == fertilizer.lower()
    ]

    if not matching.empty:
        actual = matching.iloc[0][
            ["N_percent", "P2O5_percent", "K2O_percent"]
        ].tolist()

        if actual != expected:
            grade_errors.append(fertilizer)

if not grade_errors:
    print("PASS: Basic known fertilizer grades are consistent.")
else:
    print("FAIL: Check these fertilizer grades:", grade_errors)

# Overall result
all_checks_passed = (
    not missing_columns
    and df.isnull().sum().sum() == 0
    and duplicates == 0
    and not invalid_values
    and not grade_errors
)

print("\n" + "=" * 50)

if all_checks_passed:
    print("OVERALL RESULT: ALL VALIDATION CHECKS PASSED")
else:
    print("OVERALL RESULT: PLEASE CHECK THE ERRORS")

print("Total fertilizer products:", len(df))

# Save validation report
report = pd.DataFrame({
    "Check": [
        "Required columns",
        "Missing values",
        "Duplicate fertilizer names",
        "Nutrient percentage range",
        "Known fertilizer grades"
    ],
    "Result": [
        "PASS" if not missing_columns else "FAIL",
        "PASS" if df.isnull().sum().sum() == 0 else "FAIL",
        "PASS" if duplicates == 0 else "FAIL",
        "PASS" if not invalid_values else "FAIL",
        "PASS" if not grade_errors else "FAIL"
    ]
})

output_path = Path("data/reference/fertilizer_composition_validation.csv")
report.to_csv(output_path, index=False)

print("Validation report saved:", output_path)
print("=" * 50)
