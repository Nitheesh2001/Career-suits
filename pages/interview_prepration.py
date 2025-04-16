import streamlit as st
import os
import json
import hashlib
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up Streamlit
st.set_page_config(page_title="Interview Preparation AI", page_icon="🤖")

# Paths
USERS_FILE = 'users.json'

# Session state setup
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# ------------------- Auth Helpers -------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    users = load_users()
    return users.get(username) == hash_password(password)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    save_users(users)
    return True

# ------------------ Gemini Logic --------------------
def generate_interview_preparation(job_role, resume_text, job_description, num_questions):
    prompt_template = """
You are an AI assistant specializing in interview preparation. 
Please respond ONLY in the following exact JSON format:

{
  "Interview Questions": ["question1", "question2", ...],
  "Detailed Answers": {
    "question1": "answer1",
    "question2": "answer2",
    ...
  }
}

DO NOT include any explanations or notes outside the JSON.

Here is the input data:
"""
    input_data = {
        "Job Role": job_role,
        "Resume": resume_text,
        "Job Description": job_description,
        "Number of Questions": num_questions
    }
    prompt = prompt_template + json.dumps(input_data)

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# ------------------ Pages ------------------------
def show_login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state["logged_in"] = True
            st.session_state["page"] = "home"
            st.rerun()
        else:
            st.error("Invalid username or password")

    if st.button("Sign Up"):
        st.session_state["page"] = "signup"
        st.rerun()

def show_signup_page():
    st.title("Signup")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Signup"):
        if password != confirm_password:
            st.error("Passwords do not match.")
        elif register_user(username, password):
            st.success("Signup successful! Please log in.")
            st.session_state["page"] = "login"
            st.rerun()
        else:
            st.error("Username already exists.")

    if st.button("Back to Login"):
        st.session_state["page"] = "login"
        st.rerun()

def show_main_page():
    st.title("🎯 Interview Preparation AI")
    st.subheader("Generate job-specific questions & answers")

    job_role = st.text_input("Job Role")
    uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type="pdf")
    job_description = st.text_area("Paste the Job Description")
    num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5)

    if st.button("Generate"):
        if job_role and uploaded_file and job_description:
            with st.spinner("Generating content..."):
                try:
                    resume_text = extract_text_from_pdf(uploaded_file)
                    response_text = generate_interview_preparation(job_role, resume_text, job_description, num_questions)

                    # Show raw for debug
                    st.subheader("🔍 Raw Gemini Output")
                    st.code(response_text, language="json")

                    # Parse JSON response
                    data = json.loads(response_text)
                    questions = data.get("Interview Questions", [])
                    answers = data.get("Detailed Answers", {})

                    st.subheader("📌 Questions and Answers")
                    for i, q in enumerate(questions, start=1):
                        st.markdown(f"**Q{i}: {q}**")
                        st.markdown(f"**A{i}:** {answers.get(q, 'No answer')}")

                except json.JSONDecodeError:
                    st.error("⚠️ Gemini response not in valid JSON format. Please check the raw output.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
        else:
            st.warning("Please fill in all fields and upload your resume.")

# ------------------ Routing ------------------------
if st.session_state["logged_in"]:
    if st.session_state["page"] == "home":
        show_main_page()
    else:
        st.session_state["page"] = "home"
        st.rerun()
else:
    if st.session_state["page"] == "login":
        show_login_page()
    elif st.session_state["page"] == "signup":
        show_signup_page()
    else:
        st.session_state["page"] = "login"
        st.rerun()
