from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def init_db():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            date_applied TEXT NOT NULL,
            job_link TEXT,
            referred INTEGER DEFAULT 0,
            referral_name TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/jobs", methods=["GET"])
def get_jobs():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
    jobs = cursor.fetchall()
    conn.close()
    return jsonify([dict(job) for job in jobs])


@app.route("/jobs", methods=["POST"])
def add_job():
    data = request.get_json()

    company = data.get("company")
    role = data.get("role")
    status = data.get("status")
    date_applied = data.get("date_applied")
    job_link = data.get("job_link", "")
    referred = 1 if data.get("referred") else 0
    referral_name = data.get("referral_name", "")

    if not company or not role or not status or not date_applied:
        return jsonify({"error": "Please fill in all required fields"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (company, role, status, date_applied, job_link, referred, referral_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (company, role, status, date_applied, job_link, referred, referral_name))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Job added", "id": new_id}), 201


@app.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Job deleted"})


@app.route("/jobs/<int:job_id>", methods=["PATCH"])
def update_status(job_id):
    data = request.get_json()
    new_status = data.get("status")

    if not new_status:
        return jsonify({"error": "No status provided"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = ? WHERE id = ?", (new_status, job_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Status updated"})


@app.route("/jobs/<int:job_id>/cover-letter", methods=["POST"])
def generate_cover_letter(job_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    conn.close()

    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Get the job description from the request body if provided
    data = request.get_json()
    job_description = data.get("job_description", "")

    # Build a tailored prompt if JD is provided,
    # otherwise fall back to a general one
    if job_description:
        user_message = f"""Write a cover letter for a {job['role']} position at {job['company']}.

Use the following job description to tailor the letter specifically to this role:

{job_description}

Keep it to 3 short paragraphs. Be specific about how the candidate's skills match the role requirements."""
    else:
        user_message = f"""Write a professional cover letter for a {job['role']} position at {job['company']}.
Keep it to 3 short paragraphs. Make it compelling and professional."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional cover letter writer. Write concise, compelling cover letters. Return only the cover letter text, no subject lines or extra commentary."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        cover_letter = response.choices[0].message.content
        return jsonify({"cover_letter": cover_letter})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)