import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))

# from auth import authenticate_user, register_user
from utils.auth import authenticate_user, register_user

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Read user credentials from JSON file
users_file = 'users.json'
if os.path.exists(users_file):
    with open(users_file, 'r') as f:
        try:
            users = json.load(f)
            if not isinstance(users, dict):
                st.error("Error: Invalid format in users.json.")
                users = {}
        except json.JSONDecodeError:
            st.error("Error: Failed to decode users.json.")
            users = {}
else:
    users = {}

# Prompt template for career recommendation
prompt_template = """
You are a career counselor. Based on the following details, provide a detailed career roadmap for the student.
Education: {Education}
Goals: {Goals}

Provide a step-by-step guide on how the student can achieve their career goals.
"""

def generate_career_recommendation(education, goals):
    input_data = {
        "Education": education,
        "Goals": goals
    }
    prompt = prompt_template.format(**input_data)
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text

def display_career_recommendation(recommendation):
    st.subheader("Your Career Roadmap")
    st.write(recommendation)

def show_login_page(users):

    st.title("Welcome to Career Chatbot!")
    st.subheader("Log in to explore career resources and tools designed for your success. Discover how Career Chatbot can assist you on your professional journey!")
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(username, password, users):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["page"] = "home"
            # st.experimental_rerun()
            st.rerun()
        else:
            st.error("Invalid username or password")

    if st.button("Sign Up"):
        st.session_state["page"] = "signup"
        # st.experimental_rerun()
        st.rerun()

def show_signup_page(users):
    st.title("Signup")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
    education = st.text_input("Education Background", key="signup_education")

    if st.button("Signup"):
        if password == confirm_password:
            if register_user(username, password, education, users):
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

def show_main_page():
    st.set_page_config(page_title="Career Counseling Chatbot", layout="wide")
    st.title("Career Counseling Chatbot")

    st.markdown("### Tell us about yourself")
    education = st.text_area("Education Background", placeholder="e.g., Computer Science, Commerce, Biology, Chemistry, Physics, etc.")
    goals = st.text_area("Career Goals", placeholder="e.g., Machine Learning Engineer, Software Engineer, Data Scientist, etc.")

    if st.button("Get Career Roadmap"):
        if education and goals:
            with st.spinner("Generating your career roadmap..."):
                try:
                    recommendation = generate_career_recommendation(education, goals)
                    display_career_recommendation(recommendation)
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please fill out both fields.")

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    if st.session_state["logged_in"]:
        if st.session_state["page"] == "home":
            show_main_page()
        else:
            st.session_state["page"] = "home"
            # st.experimental_rerun()
            st.rerun()
    else:
        if st.session_state["page"] == "login":
            show_login_page(users)
        elif st.session_state["page"] == "signup":
            show_signup_page(users)
        else:
            st.session_state["page"] = "login"
            # st.experimental_rerun()
            st.rerun()

if __name__ == "__main__":
    main()
