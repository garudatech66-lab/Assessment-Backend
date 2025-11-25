from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import json

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

# -----------------------------
# API Endpoint to Receive Answers
# -----------------------------
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
        answers_json = json.dumps(answers, ensure_ascii=False)

        db = get_db_connection()
        cursor = db.cursor()

        query = """
            INSERT INTO students_answers (student_id, answers_json)
            VALUES (%s, %s)
        """

        cursor.execute(query, (student_id, answers_json))
        db.commit()

        cursor.close()
        db.close()

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
