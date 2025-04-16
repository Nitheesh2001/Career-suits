import streamlit as st
import os
import json
import hashlib
from dotenv import load_dotenv
import google.generativeai as genai

# Load env vars
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set page config
st.set_page_config(
    page_title="Interview Preparation AI",
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQJL_4deHMJLHCB-63srdgaBe2JZmiOSxlnEg&s"
)

# Users file
USERS_FILE = 'users.json'

# Session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# ------------- Auth Functions -------------
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

# ------------- Gemini Generation Logic -------------
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

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

# ------------- Page Functions -------------

def show_login_page():
    st.title("Welcome to the Interview Preparation Tool!")
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
        if password == confirm_password:
            if register_user(username, password):
                st.success("Signup successful! Please log in.")
                st.session_state["page"] = "login"
                st.rerun()
            else:
                st.error("Username already exists.")
        else:
            st.error("Passwords do not match.")

    if st.button("Back to Login"):
        st.session_state["page"] = "login"
        st.rerun()

def show_main_page():
    st.title("Interview Preparation Module")
    st.subheader("Get ready for your next job interview")

    job_role = st.text_input("Job Role")
    resume_text = st.text_area("Paste Resume Text")
    job_description = st.text_area("Paste Job Description")
    num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5)

    if st.button("Generate Interview Q&A"):
        if job_role and resume_text and job_description:
            with st.spinner("Generating interview questions and answers..."):
                try:
                    response_text = generate_interview_preparation(
                        job_role, resume_text, job_description, num_questions
                    )
                    st.subheader("📄 Gemini Raw Output")
                    st.code(response_text, language="json")

                    parsed = json.loads(response_text)
                    questions = parsed.get("Interview Questions", [])
                    answers = parsed.get("Detailed Answers", {})

                    st.subheader("✅ Interview Questions and Answers")
                    for i, q in enumerate(questions, start=1):
                        st.markdown(f"**Q{i}: {q}**")
                        st.markdown(f"**A{i}: {answers.get(q, 'No answer found')}**")
                        st.write("---")
                except json.JSONDecodeError:
                    st.error("⚠️ Gemini response not in valid JSON format.")
                except Exception as e:
                    st.error(f"Error occurred: {e}")
        else:
            st.warning("Please fill all fields.")

# ------------- Page Routing -------------
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
