# 🗂️ Job Application Tracker

A full-stack AI-powered web application that helps you track job applications and generate personalised cover letters using Large Language Models (LLMs). This project demonstrates **RESTful API design**, **Database Management with SQLite**, **AI Prompt Engineering**, and **Secure Environment Management**.

## 🛠️ Tech Stack

* **Backend:** Python (Flask)
* **Frontend:** HTML5, CSS3, JavaScript (Fetch API)
* **Database:** SQLite (via Python's built-in sqlite3 module)
* **AI Engine:** OpenAI API (GPT-3.5 Turbo)
* **Environment:** Dotenv for secure API key management

## 🚀 Key Features

* **Application Tracking:** Add, update, and delete job applications with company, role, status, date, job link, and referral information.
* **Status Management:** Update application status across five stages — Applied, Interview, Final Round, Offer, and Rejected — with colour coded badges.
* **AI Cover Letter Generation:** Generate personalised cover letters tailored to each role using OpenAI. Paste the job description for a highly specific letter or leave it blank for a general one.
* **Referral Tracking:** Log whether you were referred for a role and store the referrer's name against each application.
* **Job Link Storage:** Store the job posting URL directly on each application card for quick access.
* **Robust Error Handling:** Server-side validation to manage empty inputs, missing fields, and API communication failures.
* **Security First:** Implementation of `.env` patterns to prevent sensitive credential exposure.
* **Resume-Powered Cover Letters:** Upload your PDF resume and the AI extracts 
  your actual experience, skills and education to generate a cover letter that 
  reflects who you really are — not generic filler.

## 📂 Architecture & Workflow

1. **Client-Side:** The user fills in the application form. JavaScript captures the submission event and sends a `POST` request to the `/jobs` endpoint with the application data as a JSON payload.
2. **Server-Side:** The Flask backend validates the payload, executes the appropriate SQL query against the SQLite database, and returns a JSON response.
3. **Cover Letter Generation:** When the user clicks Generate Cover Letter, a modal opens asking for an optional job description. JavaScript sends a `POST` request to `/jobs/<id>/cover-letter`. Flask constructs a structured prompt using the job details and job description, calls the OpenAI API, and returns the generated letter.
4. **Response:** All results are rendered dynamically on the UI without a page refresh.

## ⚙️ Getting Started

### Prerequisites

* Python 3.10+
* OpenAI API Key

### Installation & Setup

1. **Clone the repository:**
```bash
   git clone https://github.com/Arpit120200/job-application-tracker.git
   cd job-application-tracker
```

2. **Install dependencies:**
```bash
   pip install flask flask-cors openai python-dotenv
```

3. **Configure environment variables:**
   Create a `.env` file in the root directory and add your key:
```bash
   OPENAI_API_KEY=your_api_key_here
```

4. **Run the application:**
```bash
   python app.py
```

5. **Access the UI:**
   Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)
