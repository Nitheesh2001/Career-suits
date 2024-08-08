import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import hashlib
from utils.auth import authenticate_user, register_user  # Import authentication functions

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Interview Preparation AI", page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQJL_4deHMJLHCB-63srdgaBe2JZmiOSxlnEg&s")  # Set the favicon here


# Configure Google Generative AI API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# Path to the users file
USERS_FILE = 'users.json'

# Function to load users from JSON file
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Function to save users to JSON file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Function to hash a password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to authenticate user
def authenticate_user(username, password):
    users = load_users()
    hashed_password = hash_password(password)
    if username in users:
        return users[username] == hashed_password
    return False

# Function to register a new user
def register_user(username, password):
    users = load_users()
    hashed_password = hash_password(password)
    if username in users:
        return False  # Username already exists
    users[username] = hashed_password
    save_users(users)
    return True

# Function to generate interview preparation materials
def generate_interview_preparation(job_role, experience_level, job_description, num_questions):
    prompt_template = """
    You are an AI assistant specializing in interview preparation. Provide a list of exactly {num_questions} common interview questions 
    and detailed answers based on the given job role, experience level, job description, and number of questions. 
    Provide the questions and answers in the following format:
    Question 1:
    [Question]
    Answer 1:
    [Answer]
    Question 2:
    [Question]
    Answer 2:
    [Answer]
    ...
    """
    input_data = f"""
    Job Role: {job_role}
    Experience Level: {experience_level}
    Job Description: {job_description}
    Number of Questions: {num_questions}
    """
    prompt = prompt_template.format(num_questions=num_questions) + input_data
    response = genai.generate_text(model="models/text-bison-001", prompt=prompt)

    st.write("API Response:", response.result)  # Log the raw API response

    try:
        response_text = response.result.strip()
        qa_pairs = []
        question = None
        answer = None

        lines = response_text.split('\n')
        for line in lines:
            if line.startswith("Question"):
                if question and answer:
                    qa_pairs.append((question, answer))
                question = line.split(":", 1)[1].strip()
                answer = None
            elif line.startswith("Answer"):
                answer = line.split(":", 1)[1].strip()
                if question and answer:
                    qa_pairs.append((question, answer))
                    question = None
                    answer = None

        # Append the last QA pair if it's valid
        if question and answer:
            qa_pairs.append((question, answer))

        return qa_pairs[:num_questions]
    except Exception as e:
        st.error("An unexpected error occurred while processing the response.")
        st.write("Error details:", str(e))  # Log the error details
        return None

# Function to show the login page
def show_login_page():
    st.title("Welcome to the Interview Preparation Tool!")
    st.subheader("Log in to access tailored resources and practice questions. Boost your confidence and ace your next interview!")
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state["logged_in"] = True
            st.session_state["page"] = "home"
            # st.experimental_rerun()
            st.rerun()
        else:
            st.error("Invalid username or password")

    if st.button("Sign Up"):
        st.session_state["page"] = "signup"
        # st.experimental_rerun()
        st.rerun()

# Function to show the signup page
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
                # st.experimental_rerun()
                st.rerun()
            else:
                st.error("Signup failed. Username might already exist.")
        else:
            st.error("Passwords do not match.")

    if st.button("Back to Login"):
        st.session_state["page"] = "login"
        # st.experimental_rerun()
        st.rerun()

# Function to show the main content page
def show_main_page():
    st.title("Interview Preparation Module")
    st.subheader("Get ready for your next job interview with tailored questions and answers")

    st.markdown("### Enter the job role, experience level, and job description to receive customized interview questions and answers")

    job_role = st.text_input("Job Role", key="job_role")
    experience_level = st.selectbox("Experience Level", [i for i in range(31)], key="experience_level")
    job_description = st.text_area("Paste the Job Description", key="job_description")
    num_questions = st.number_input("Number of Questions", min_value=1, max_value=50, value=10, step=1, key="num_questions")

    if st.button("Generate Interview Questions and Answers"):
        if job_role and experience_level is not None and job_description:
            with st.spinner("Generating interview preparation materials..."):
                try:
                    qa_pairs = generate_interview_preparation(job_role, experience_level, job_description, num_questions)
                    if qa_pairs:
                        st.subheader("Interview Preparation Materials:")

                        # Display questions and answers one by one
                        for i, (question, answer) in enumerate(qa_pairs):
                            st.write(f"**Question {i+1}:**")
                            st.write(question)
                            st.write(f"**Answer:**")
                            st.write(answer)
                            st.write("---")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please enter the job role, experience level, and job description.")

# Display the appropriate page based on login status
if st.session_state["logged_in"]:
    if st.session_state["page"] == "home":
        show_main_page()
    else:
        st.session_state["page"] = "home"
        # st.experimental_rerun()
        st.rerun()
else:
    if st.session_state["page"] == "login":
        show_login_page()
    elif st.session_state["page"] == "signup":
        show_signup_page()
    else:
        st.session_state["page"] = "login"
        # st.experimental_rerun()
        st.rerun()
