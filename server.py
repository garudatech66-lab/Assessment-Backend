from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector
import json
import openpyxl

from pymongo import MongoClient
import os

from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# Connect to MongoDB
mongo_url = os.getenv("MONGO_URL")
mongo_db = os.getenv("MONGO_DB", "examdb")
mongo_collection = os.getenv("MONGO_COLLECTION", "students_answers")

client = MongoClient(mongo_url)
db = client[mongo_db]
collection = db[mongo_collection]




app = Flask(__name__)

# Enable CORS for all domains (use origins list to restrict)
# To allow all domains:
CORS(app, resources={r"/*": {"origins": "*"}})

# If you want to allow only specific domains, replace "*" with a list:
# CORS(app, resources={r"/*": {"origins": ["https://example.com", "http://localhost:3000"]}})

# -----------------------------
# MySQL Connection Function
# -----------------------------
def get_db_connection():
     return mysql.connector.connect(
        host="localhost",
        user="root",          # your MySQL username
        password="Thulasi@123", # your MySQL password
        database="mydb"    # your database name
    )
    # local testing
    # return mysql.connector.connect(
    #     host="localhost",
    #     user="root",          # your MySQL username
    #     password="Thulasi@123", # your MySQL password
    #     database="mydb"    # your database name
    # )

# -----------------------------
# API Endpoint to Receive Answers
# -----------------------------
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"status": "error", "message": "Username & password required"}), 400

        # Load Excel file
        workbook = openpyxl.load_workbook("./usersdata.xlsx")
        sheet = workbook.active

        # Find user
        user_found = False
        correct_password = None

        for row in sheet.iter_rows(min_row=2, values_only=True):  
            print(row)
            excel_username = str(row[7]).strip()  # Column H
            excel_password = str(row[8]).strip()  # Column I
            # print(excel_username, excel_password, username, password)
            if username == excel_username:
                user_found = True
                correct_password = excel_password
                break

        if not user_found:
            return jsonify({"status": "error", "message": "User not found"}), 404

        if password != correct_password:
            print(password, correct_password)
            return jsonify({"status": "error", "message": "Invalid password"}), 401

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "user": username,
            "token": "dummy-jwt-token"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/clearDBData', methods=['DELETE'])
def clear_db_data():
    result = collection.delete_many({})
    return {"message": "Collection cleared", "deleted_count": result.deleted_count}, 200


@app.route('/download-pdf')
def download_pdf():
    data = list(collection.find({}, {"_id": 0}))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("MongoDB Data Export", styles['Title']))
    elements.append(Spacer(1, 20))

    # Add each document nicely formatted
    for record in data:
        formatted = "<br/>".join([f"<b>{k}</b>: {v}" for k, v in record.items()])
        elements.append(Paragraph(formatted, styles['Normal']))
        elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        download_name="data.pdf",
        as_attachment=True,
        mimetype="application/pdf"
    )

@app.route('/submit', methods=['POST'])
def submit_answers():
    try:
        data = request.get_json(force=True)  # parse JSON body

        # Extract student ID if provided; keep None if not present
        student_id = data.get("student_id")

        # Remove student_id from answers dictionary so answers contain only numbered keys
        answers = {k: v for k, v in data.items() if k != "student_id"}

        # Basic validation: ensure we have at least one answer
        if not answers:
            return jsonify({"status": "error", "message": "No answers found in request"}), 400

        # Convert answers to JSON string for storage
        # answers_json = json.dumps(answers, ensure_ascii=False)

        # db = get_db_connection()
        # cursor = db.cursor()

        # query = """
        #    INSERT INTO students_answers (student_id, answers_json)
        #    VALUES (%s, %s)
        # """

        # cursor.execute(query, (student_id, answers_json))
        # db.commit()

        # cursor.close()
        # db.close()

        # Insert into MongoDB
        record = {
            "student_id": student_id,
            "answers": answers
        }
        result = collection.insert_one(record)

        return jsonify({"status": "success", "message": "Answers saved!"}), 201

    except mysql.connector.Error as db_err:
        # more informative DB error
        return jsonify({"status": "error", "message": f"MySQL error: {str(db_err)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
     

# -----------------------------
# Start Server
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)




