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

    # Get the job description text from the form data
    job_description = request.form.get("job_description", "").strip()

    # Extract text from the uploaded resume PDF if provided
    resume_text = ""
    if "resume" in request.files:
        resume_file = request.files["resume"]

        # Only process if the file is actually a PDF
        if resume_file.filename.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                import io

                # Read the file into memory — no need to save it to disk
                pdf_bytes = io.BytesIO(resume_file.read())
                reader = PdfReader(pdf_bytes)

                # Extract text from every page and join it together
                for page in reader.pages:
                    resume_text += page.extract_text() or ""

                resume_text = resume_text.strip()

            except Exception as e:
                return jsonify({"error": f"Could not read PDF: {str(e)}"}), 400

    # Build the prompt based on what the user provided
    # Four scenarios: both JD and resume, only JD, only resume, neither
    if resume_text and job_description:
        user_message = f"""Write a personalised cover letter for someone applying for a {job['role']} position at {job['company']}.

Here is the candidate's resume:
{resume_text}

Here is the job description:
{job_description}

Instructions:
- Write 3 short paragraphs
- Match the candidate's actual experience from the resume to the specific requirements in the job description
- Be specific — reference real skills, projects or experience from the resume
- Sound human and natural, not generic
- Return only the cover letter text, no subject line or extra commentary"""

    elif resume_text:
        user_message = f"""Write a professional cover letter for someone applying for a {job['role']} position at {job['company']}.

Here is the candidate's resume:
{resume_text}

Instructions:
- Write 3 short paragraphs
- Draw on the candidate's actual experience and skills from the resume
- Tailor the letter to the role and company
- Return only the cover letter text"""

    elif job_description:
        user_message = f"""Write a cover letter for a {job['role']} position at {job['company']}.

Here is the job description:
{job_description}

Instructions:
- Write 3 short paragraphs
- Address the key requirements in the job description
- Make it compelling and specific
- Return only the cover letter text"""

    else:
        user_message = f"""Write a professional cover letter for a {job['role']} position at {job['company']}.

Instructions:
- Write 3 short paragraphs
- Make it compelling and professional
- Return only the cover letter text"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert cover letter writer. Write personalised, compelling cover letters that sound human and specific. Never use generic filler phrases like 'I am writing to express my interest'."
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