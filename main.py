from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
import mysql.connector

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
load_dotenv()

# ==========================================
# LOAD MODEL
# ==========================================

with open("Model/OEE_Tomorrow_Model.pkl", "rb") as file:
    saved_data = pickle.load(file)

model = saved_data["model"]

features = saved_data["features"]

print("Model loaded successfully!")

print("Features used by model:")

print(features)


# ==========================================
# MYSQL CONNECTION
# ==========================================

def get_db_connection():
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    # Check that required environment variables exist
    if not all([db_host, db_user, db_password, db_name]):
        raise ValueError(
            "Missing database settings. Check your .env file."
        )

    connection = mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        connection_timeout=10
    )

    return connection

# def get_db_connection():

#     connection = mysql.connector.connect(
#         host=os.getenv("DB_HOST"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         database=os.getenv("DB_NAME")
#     )

#     return connection


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# PREDICT
# ==========================================

@app.route("/predict", methods=["POST"])
def predict():

    # ==========================================
    # GET USER INPUT
    # ==========================================

    data = request.get_json()

    # Check whether JSON data was provided
    if not data:
        return jsonify({
            "error": "No input data provided"
        }), 400


    # ==========================================
    # REQUIRED FEATURES
    # ==========================================

    required_fields = [
        "Machine_Age",
        "OEE_Lag_1",
        "Avail_Hrs_Lag_1",
        "MC_Running_Hrs_Lag_1",
        "Total_DT_Lag_1",
        "Prod_Qty_Lag_1",
        "Rej_Qty_Lag_1",
        "Maintenance_Flag_Lag_1"
    ]


    # ==========================================
    # CHECK MISSING FIELDS
    # ==========================================

    missing_fields = [
        field for field in required_fields
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "missing_fields": missing_fields
        }), 400


    # ==========================================
    # CHECK DATA TYPES
    # ==========================================

    numeric_fields = [
        "Machine_Age",
        "OEE_Lag_1",
        "Avail_Hrs_Lag_1",
        "MC_Running_Hrs_Lag_1",
        "Total_DT_Lag_1",
        "Prod_Qty_Lag_1",
        "Rej_Qty_Lag_1"
    ]

    for field in numeric_fields:

        if not isinstance(data[field], (int, float)):

            return jsonify({
                "error": "Invalid data type",
                "field": field,
                "message": f"{field} must be a number"
            }), 400

  
    # ==========================================
    # CHECK NUMERIC RANGES
    # ==========================================

    if data["Machine_Age"] < 0:
        return jsonify({
        "error": "Invalid value",
        "field": "Machine_Age",
        "message": "Machine_Age cannot be negative"
        }), 400


    if not 0 <= data["OEE_Lag_1"] <= 100: 
        return jsonify({
        "error": "Invalid value",
        "field": "OEE_Lag_1",
        "message": "OEE_Lag_1 must be between 0 and 100"
        }), 400


    if data["Avail_Hrs_Lag_1"] < 0:
        return jsonify({
        "error": "Invalid value",
        "field": "Avail_Hrs_Lag_1",
        "message": "Avail_Hrs_Lag_1 cannot be negative"
        }), 400


    if data["MC_Running_Hrs_Lag_1"] < 0:
        return jsonify({
        "error": "Invalid value",
        "field": "MC_Running_Hrs_Lag_1",
        "message": "MC_Running_Hrs_Lag_1 cannot be negative"
        }), 400


    if data["Total_DT_Lag_1"] < 0:
        return jsonify({
        "error": "Invalid value",
        "field": "Total_DT_Lag_1",
        "message": "Total_DT_Lag_1 cannot be negative"
        }), 400


    if data["Prod_Qty_Lag_1"] < 0:
        return jsonify({
        "error": "Invalid value",
        "field": "Prod_Qty_Lag_1",
        "message": "Prod_Qty_Lag_1 cannot be negative"
        }), 400


    if data["Rej_Qty_Lag_1"] < 0:
        return jsonify({
        "error": "Invalid value",
        "field": "Rej_Qty_Lag_1",
        "message": "Rej_Qty_Lag_1 cannot be negative"
        }), 400

    # ==========================================
    # CHECK MAINTENANCE FLAG
    # ==========================================

    if data["Maintenance_Flag_Lag_1"] not in [0, 1]:

        return jsonify({
            "error": "Invalid value",
            "field": "Maintenance_Flag_Lag_1",
            "message": "Maintenance_Flag_Lag_1 must be 0 or 1"
        }), 400


    # ==========================================
    # CONVERT INPUT INTO DATAFRAME
    # ==========================================

    input_data = pd.DataFrame([data])


    # ==========================================
    # ARRANGE FEATURES IN CORRECT ORDER
    # ==========================================

    input_data = input_data[features]


    # ==========================================
    # MAKE PREDICTION
    # ==========================================

    prediction = model.predict(input_data)

    predicted_oee = round(float(prediction[0]), 2)

    print("Predicted OEE:", predicted_oee)


    # ==========================================
    # SAVE INTO MYSQL
    # ==========================================

    connection = get_db_connection()

    cursor = connection.cursor()

    query = """
    INSERT INTO predictions (
        machine_age,
        oee_lag_1,
        avail_hrs_lag_1,
        mc_running_hrs_lag_1,
        total_dt_lag_1,
        prod_qty_lag_1,
        rej_qty_lag_1,
        maintenance_flag_lag_1,
        predicted_oee
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        data["Machine_Age"],
        data["OEE_Lag_1"],
        data["Avail_Hrs_Lag_1"],
        data["MC_Running_Hrs_Lag_1"],
        data["Total_DT_Lag_1"],
        data["Prod_Qty_Lag_1"],
        data["Rej_Qty_Lag_1"],
        data["Maintenance_Flag_Lag_1"],
        predicted_oee
    )

    cursor.execute(query, values)

    connection.commit()

    cursor.close()

    connection.close()


    # ==========================================
    # RETURN RESPONSE
    # ==========================================

    return jsonify({
        "message": "Prediction successful and saved to MySQL",
        "predicted_oee": predicted_oee
    })


# ==========================================
# GET ALL SAVED PREDICTIONS
# ==========================================

@app.route("/predictions", methods=["GET"])
def get_predictions():

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM predictions
        ORDER BY created_at DESC
    """)

    records = cursor.fetchall()

    cursor.close()

    connection.close()

    return jsonify(records)


# ==========================================
# RUN FLASK
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)