
import pandas as pd
import numpy as np
import os
import joblib
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

print("MACHINE LEARNING MODEL TRAINING")
print("====================================")

# STEP 1: LOAD PREPROCESSED DATA

X_train = pd.read_csv(
    "data/processed/preprocessed/X_train_encoded.csv"
)

X_test = pd.read_csv(
    "data/processed/preprocessed/X_test_encoded.csv"
)

y_train = pd.read_csv(
    "data/processed/preprocessed/y_train.csv"
).iloc[:, 0]

y_test = pd.read_csv(
    "data/processed/preprocessed/y_test.csv"
).iloc[:, 0]

print("\nDatasets loaded successfully!")
print("Training features:", X_train.shape)
print("Testing features:", X_test.shape)

# STEP 2: CREATE MACHINE LEARNING MODELS

models = {
    "Decision Tree": DecisionTreeClassifier(
        random_state=42,
        class_weight="balanced"
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced"
    ),

    "KNN": KNeighborsClassifier(
        n_neighbors=5
    ),

    "SVM": SVC(
        probability=True,
        class_weight="balanced",
        random_state=42
    )
}

# STEP 3: TRAIN, PREDICT AND EVALUATE MODELS

results = []

os.makedirs("models", exist_ok=True)
os.makedirs("outputs/model_evaluation", exist_ok=True)

best_model = None
best_model_name = ""
best_f1_score = -1

for name, model in models.items():

    print("\n====================================")
    print("Training:", name)

    # Train the model
    model.fit(X_train, y_train)

    # Predict fertilizer types
    predictions = model.predict(X_test)

    # Calculate evaluation metrics
    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test, predictions,
        average="macro",
        zero_division=0
    )

    recall = recall_score(
        y_test, predictions,
        average="macro",
        zero_division=0
    )

    f1 = f1_score(
        y_test, predictions,
        average="macro",
        zero_division=0
    )

    print("\nModel:", name)
    print("Accuracy:", round(accuracy * 100, 2), "%")
    print("Macro Precision:", round(precision, 3))
    print("Macro Recall:", round(recall, 3))
    print("Macro F1 Score:", round(f1, 3))

    # Save results
    results.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1
    })

    # Print detailed classification report
    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    # Save confusion matrix
    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=model.classes_
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=model.classes_
    )

    fig, ax = plt.subplots(figsize=(12, 10))
    display.plot(
        ax=ax,
        xticks_rotation=90,
        cmap="Blues",
        colorbar=False
    )

    plt.title(name + " Confusion Matrix")
    plt.tight_layout()

    file_name = name.lower().replace(" ", "_")
    plt.savefig(
        "outputs/model_evaluation/" + file_name + "_confusion_matrix.png"
    )
    plt.close()

    # Select the best model using macro F1 score
    if f1 > best_f1_score:
        best_f1_score = f1
        best_model = model
        best_model_name = name

# STEP 4: COMPARE ALL MODELS

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="F1 Score",
    ascending=False
)

print("\n====================================")
print("FINAL MODEL COMPARISON")
print("====================================")
print(results_df.to_string(index=False))

# Save comparison table
results_df.to_csv(
    "outputs/model_evaluation/model_comparison.csv",
    index=False
)

# STEP 5: SAVE THE BEST MODEL

joblib.dump(
    best_model,
    "models/best_model.pkl"
)

print("\n====================================")
print("BEST MODEL:", best_model_name)
print("Best Macro F1 Score:", round(best_f1_score, 3))
print("Best model saved as models/best_model.pkl")

print("\nConfusion matrices saved in:")
print("outputs/model_evaluation/")

print("\nModel comparison saved in:")
print("outputs/model_evaluation/model_comparison.csv")

print("\nSTEP 10 COMPLETED SUCCESSFULLY!")
print("====================================")
