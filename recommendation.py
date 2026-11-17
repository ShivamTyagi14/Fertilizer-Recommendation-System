
import pandas as pd
import joblib

print("SMART FERTILIZER RECOMMENDATION SYSTEM")
print("========================================")

# STEP 1: LOAD TRAINED MODEL AND PREPROCESSOR

model = joblib.load("models/best_model.pkl")
preprocessor = joblib.load("models/preprocessor.pkl")

# Load cleaned dataset to get available soil and crop types
data = pd.read_csv("data/processed/fertilizer_cleaned.csv")

soil_types = sorted(data["Soil_Type"].unique())
crop_types = sorted(data["Crop_Type"].unique())

print("\nModel loaded successfully!")

# STEP 2: GET USER INPUT

def get_choice(message, choices):

    print("\nAvailable options:")

    for choice in choices:
        print("-", choice)

    while True:
        value = input(message).strip()

        for choice in choices:
            if value.lower() == choice.lower():
                return choice

        print("Please enter one of the available options.")


def get_number(message):

    while True:
        try:
            return float(input(message))
        except ValueError:
            print("Please enter a valid number.")


print("\nENTER SOIL AND ENVIRONMENT DETAILS")

temperature = get_number("Enter Temperature: ")
humidity = get_number("Enter Humidity: ")
moisture = get_number("Enter Moisture: ")

soil_type = get_choice("Enter Soil Type: ", soil_types)
crop_type = get_choice("Enter Crop Type: ", crop_types)

nitrogen = get_number("Enter Nitrogen value: ")
potassium = get_number("Enter Potassium value: ")
phosphorous = get_number("Enter Phosphorous value: ")

# STEP 3: CREATE INPUT DATAFRAME

user_data = pd.DataFrame([{
    "Temparature": temperature,
    "Humidity": humidity,
    "Moisture": moisture,
    "Soil_Type": soil_type,
    "Crop_Type": crop_type,
    "Nitrogen": nitrogen,
    "Potassium": potassium,
    "Phosphorous": phosphorous
}])

# STEP 4: PREPROCESS USER INPUT

encoded_data = preprocessor.transform(user_data)

if hasattr(encoded_data, "toarray"):
    encoded_data = encoded_data.toarray()

encoded_data = pd.DataFrame(
    encoded_data,
    columns=preprocessor.get_feature_names_out()
)

# STEP 5: PREDICT TOP 3 FERTILIZERS

scores = model.predict_proba(encoded_data)[0]

fertilizer_names = model.classes_

ranked_indices = scores.argsort()[::-1][:3]

print("\n========================================")
print("TOP 3 FERTILIZER RECOMMENDATIONS")
print("========================================")

for rank, index in enumerate(ranked_indices, start=1):

    fertilizer = fertilizer_names[index]
    score = scores[index] * 100

    print("\nRank:", rank)
    print("Fertilizer:", fertilizer)
    print("Model Score:", round(score, 2), "%")

# STEP 6: DISPLAY INPUT SUMMARY

print("\n========================================")
print("USER INPUT SUMMARY")
print("========================================")

print("Temperature:", temperature)
print("Humidity:", humidity)
print("Moisture:", moisture)
print("Soil Type:", soil_type)
print("Crop Type:", crop_type)
print("Nitrogen:", nitrogen)
print("Potassium:", potassium)
print("Phosphorous:", phosphorous)

print("\nRECOMMENDATION COMPLETED!")
print("========================================")
