import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from utils.auth import authenticate_user, register_user  # Import authentication functions

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Questions for the quiz with placeholders
questions = {
    "Teamwork": ("Please rate your teamwork skills from 1 to 5 and provide a brief example of a team project you have worked on.", "Rate from 1 to 5, and describe a team project"),
    "Problem Solving": ("Please rate your problem-solving skills from 1 to 5 and describe a situation where you solved a difficult problem.", "Rate from 1 to 5, and describe a problem-solving situation"),
    "Communication": ("Please rate your communication skills from 1 to 5 and share an experience where effective communication was crucial.", "Rate from 1 to 5, and describe a communication experience"),
    "Adaptability": ("Please rate your adaptability from 1 to 5 and give an example of how you adapted to a new situation.", "Rate from 1 to 5, and describe an adaptable situation"),
    "Critical Thinking": ("Please rate your critical thinking skills from 1 to 5 and provide an example of a time you used critical thinking.", "Rate from 1 to 5, and describe a critical thinking example"),
    "Time Management": ("Please rate your time management skills from 1 to 5 and describe how you manage your time effectively.", "Rate from 1 to 5, and describe time management strategies"),
    "Interpersonal": ("Please rate your interpersonal skills from 1 to 5 and share an example of how you interact with others in a professional setting.", "Rate from 1 to 5, and describe an interpersonal interaction")
}

# Function to get feedback from Gemini API
def get_feedback(answers):
    questions_and_answers = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()])
    prompt = f"""
    Based on the following self-assessment of soft skills, provide a detailed analysis and suggestions for improvement.
    {questions_and_answers}
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

# Resources for improvement
resources = {
    "Teamwork": [
        "https://www.youtube.com/watch?v=D3KJufY9r4I",  # Video on teamwork skills by Team Performance
        "https://www.thebalancecareers.com/importance-of-teamwork-1918016"  # Document on teamwork
    ],
    "Problem Solving": [
        "https://www.youtube.com/watch?v=hiqoCvPs_Jc",  # Video on problem-solving skills by Skillshare
        "https://www.mindtools.com/pages/article/newHTE_00.htm"  # Document on problem-solving
    ],
    "Communication": [
        "https://www.youtube.com/watch?v=3ML_uBKpD6Y",  # Video on communication skills by TEDx Talks
        "https://www.skillsyouneed.com/ips/communication-skills.html"  # Document on communication
    ],
    "Adaptability": [
        "https://www.youtube.com/watch?v=G3DUzXGkzyM",  # Video on adaptability skills by Harvard Business Review
        "https://www.indeed.com/career-advice/career-development/adaptability-skills"  # Document on adaptability
    ],
    "Critical Thinking": [
        "https://www.youtube.com/watch?v=c6IyuI8TT54",  # Video on critical thinking by Critical Thinking Academy
        "https://www.verywellmind.com/what-is-critical-thinking-2794963"  # Document on critical thinking
    ],
    "Time Management": [
        "https://www.youtube.com/watch?v=WXBA4eWskrc",  # Video on time management skills by Project Better Self
        "https://www.thebalancecareers.com/time-management-tips-1918537"  # Document on time management
    ],
    "Interpersonal": [
        "https://www.youtube.com/watch?v=6Gp2x-Q6jc8&list=PLLy_2iUCG87DsAOykzkgjl0XqGgPmyY4P",  # Video on interpersonal skills by BetterHelp
        "https://dharwad.kvs.ac.in/sites/default/files/VRK%2C%20LIFE%20SKILLS.pdf"  # Document on interpersonal skills
    ]
}

# Descriptions of why each skill is important
descriptions = {
    "Teamwork": "Teamwork is crucial for achieving collective goals, enhancing productivity, and fostering a collaborative environment.",
    "Problem Solving": "Problem-solving skills enable individuals to effectively tackle challenges and find innovative solutions.",
    "Communication": "Effective communication is essential for sharing information, building relationships, and ensuring clarity.",
    "Adaptability": "Adaptability helps individuals adjust to new circumstances, remain flexible, and thrive in changing environments.",
    "Critical Thinking": "Critical thinking involves analyzing situations, making informed decisions, and solving problems logically.",
    "Time Management": "Time management skills help prioritize tasks, meet deadlines, and maintain a healthy work-life balance.",
    "Interpersonal": "Interpersonal skills facilitate positive interactions, teamwork, and collaboration in professional settings."
}

def show_login_page():
    st.title("Welcome to the Soft Skills Assessment!")
    st.subheader("Log in to evaluate and enhance your soft skills. Gain valuable insights to boost your interpersonal effectiveness and career success!")

    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            with open('users.json', 'r') as f:
                users = json.load(f)
            if authenticate_user(username, password, users):
                st.session_state["logged_in"] = True
                st.session_state["page"] = "main"
                # st.experimental_rerun()
                st.rerun()
            else:
                st.error("Invalid username or password")
        except FileNotFoundError:
            st.error("User database not found. Please contact support.")
        except json.JSONDecodeError:
            st.error("Error reading user database. Please contact support.")

    if st.button("Sign Up"):
        st.session_state["page"] = "signup"
        # st.experimental_rerun()
        st.rerun()

def show_signup_page():
    st.title("Signup")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Signup"):
        try:
            with open('users.json', 'r') as f:
                users = json.load(f)
        except FileNotFoundError:
            users = {}
        
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

def show_main_page():
    st.set_page_config(page_title="Soft Skills Assessment", layout="wide")
    st.title("Soft Skills Assessment")

    # Collect user input
    st.header("Answer the following questions to assess your soft skills")
    answers = {}
    for skill, (question, placeholder) in questions.items():
        answer = st.text_area(skill, placeholder=placeholder)
        answers[skill] = answer

    # Button to submit the form
    if st.button("Get Feedback"):
        if all(answers.values()):
            with st.spinner("Generating your soft skills assessment..."):
                try:
                    feedback = get_feedback(answers)
                    st.subheader("Your Soft Skills Feedback")
                    st.write(feedback)
                    
                    # Display resources for improvement
                    st.subheader("Resources for Improvement")
                    for skill, answer in answers.items():
                        rating = int(answer.split()[0]) if answer.split() else 0
                        if rating < 4:  # Assuming a rating less than 4 indicates a need for improvement
                            st.markdown(f"### {skill}")
                            st.write(descriptions[skill])
                            for resource in resources[skill]:
                                st.write(resource)
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
        show_main_page()
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
