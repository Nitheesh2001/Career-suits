import streamlit as st
from fpdf import FPDF
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

from utils.auth import authenticate_user, register_user  # Import authentication functions

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get resume content
def get_resume_content(name, email, phone, education, experience, skills, projects):
    prompt = f"""
    You are a professional resume builder. Based on the following details, create a well-structured resume.
    Name: {name}
    Email: {email}
    Phone: {phone}
    Education: {education}
    Experience: {experience}
    Skills: {skills}
    Projects: {projects}
    
    Provide a detailed and formatted resume.
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

# Function to generate PDF
def generate_pdf(resume_content, filename="resume.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in resume_content.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True, align='L')

    pdf.output(filename)
    return filename

# Function to load users from file
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    else:
        return {}

# Function to show the login page
def show_login_page():
    st.title("Welcome to the Resume Builder!")
    st.subheader("Log in to craft impressive resumes effortlessly. Highlight your skills and experience to make a standout impression on employers!")

    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()  # Load users here
        if authenticate_user(username, password, users):
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
        users = load_users()  # Load users here
        if password == confirm_password:
            if register_user(username, password, users):
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
    st.set_page_config(page_title="Resume Builder", layout="wide")
    st.title("Resume Builder")

    # Collect user input
    st.header("Enter your details")
    name = st.text_input("Full Name", placeholder="e.g., John Doe")
    email = st.text_input("Email", placeholder="e.g., john.doe@example.com")
    phone = st.text_input("Phone", placeholder="e.g., +1234567890")
    education = st.text_area("Education", placeholder="e.g., B.Sc. in Computer Science from XYZ University")
    experience = st.text_area("Experience", placeholder="e.g., Software Engineer at ABC Corp. (2018-2022)")
    skills = st.text_area("Skills", placeholder="e.g., Python, Machine Learning, Data Analysis")
    projects = st.text_area("Projects", placeholder="e.g., AI Chatbot, E-commerce Website")

    # Button to submit the form
    if st.button("Generate Resume"):
        if name and email and phone and education and experience and skills and projects:
            with st.spinner("Generating your resume..."):
                try:
                    resume_content = get_resume_content(name, email, phone, education, experience, skills, projects)
                    st.subheader("Your Resume")
                    st.text(resume_content)
                    
                    # Generate and provide download link for PDF
                    pdf_filename = generate_pdf(resume_content)
                    with open(pdf_filename, "rb") as file:
                        st.download_button(
                            label="Download Resume as PDF",
                            data=file,
                            file_name="resume.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please fill out all the fields.")

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
            show_login_page()
        elif st.session_state["page"] == "signup":
            show_signup_page()
        else:
            st.session_state["page"] = "login"
            # st.experimental_rerun()
            st.rerun()

if __name__ == "__main__":
    main()
