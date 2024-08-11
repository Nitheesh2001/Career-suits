import streamlit as st
import pyttsx3
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import os
from dotenv import load_dotenv
import google.generativeai as genai
import threading
import queue
import json
from utils.auth import authenticate_user, register_user
from scipy.io.wavfile import write

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize recognizer
recognizer = sr.Recognizer()

# Path to users JSON file
USERS_FILE = "users.json"

# Function to load users from JSON file
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

# Function to get feedback from Gemini API
def get_feedback(answer, context):
    prompt = f"""
    Context: {context}
    Answer: {answer}

    Provide feedback on the answer and suggest areas of improvement.
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

# Function to generate follow-up question based on previous answer
def generate_followup_question(previous_answer):
    prompt = f"""
    Based on the following answer, generate a follow-up question.
    Answer: {previous_answer}
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

# Function to capture audio response and convert to text
def get_audio_response(q):
    sample_rate = 44100  # Sample rate in Hz
    duration = 5  # Duration of the recording in seconds
    st.write("Listening for your response...")

    # Record the audio using sounddevice
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait until the recording is finished

    # Save the recorded audio to a WAV file
    wav_file = "output.wav"
    write(wav_file, sample_rate, audio_data)

    # Use SpeechRecognition to process the WAV file
    with sr.AudioFile(wav_file) as source:
        audio = recognizer.record(source)
        try:
            response = recognizer.recognize_google(audio)
            q.put(response)
        except sr.UnknownValueError:
            q.put("Could not understand audio")
        except sr.RequestError as e:
            q.put(f"Could not request results; {e}")

# Function to generate initial questions based on user input
def generate_initial_questions(job_type, experience_level, interview_format, focus_areas):
    initial_questions = [
        f"Tell me about your experience in {job_type}.",
        f"What are your strengths and weaknesses as a {experience_level} professional?",
        f"How do you prepare for a {interview_format} interview?",
        f"What are the key focus areas in {focus_areas}?"
    ]
    return initial_questions

# Function to handle login page
def login_page():
    st.title("Welcome to the Mock Interview!")
    st.subheader("Log in to simulate real interview scenarios and receive feedback. Sharpen your skills and get ready to impress!")
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_users()
        if authenticate_user(username, password, users):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["page"] = "home"
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    if st.button("Sign Up"):
        st.session_state["page"] = "signup"
        st.rerun()

# Function to handle signup page
def signup_page():
    st.title("Sign Up")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
    if st.button("Sign Up"):
        users = load_users()
        if password == confirm_password:
            if register_user(username, password, users):
                st.success("Signup successful! You can now log in.")
                st.session_state["page"] = "login"
                st.rerun()
            else:
                st.error("Username already exists.")
        else:
            st.error("Passwords do not match.")
    if st.button("Back to Login"):
        st.session_state["page"] = "login"
        st.rerun()

# Function to handle home page and mock interview
def home_page():
    # Streamlit app
    st.set_page_config(page_title="Mock Interview with AI Feedback", layout="wide")
    st.title("Mock Interview with AI Feedback")

    # Collect user input
    st.header("Tell us about yourself")
    job_type = st.text_area("Job or Industry", placeholder="e.g., software engineering, marketing, finance, healthcare, etc.")
    experience_level = st.text_area("Current Level of Experience", placeholder="e.g., entry-level, mid-level, senior-level, executive-level")
    interview_format = st.text_area("Preferred Interview Format", placeholder="e.g., behavioral, technical, case study, panel interview")
    focus_areas = st.text_area("Specific Focus Areas", placeholder="e.g., common interview questions, salary negotiation, body language")

    # Initialize session state
    if 'questions' not in st.session_state:
        st.session_state.questions = generate_initial_questions(job_type, experience_level, interview_format, focus_areas)
        st.session_state.current_question = 0
        st.session_state.responses = []
        st.session_state.current_response = ""
        st.session_state.recording = False
        st.session_state.total_feedback = []
        st.session_state.interview_started = False

    # Button to start the mock interview
    if st.button("Start Mock Interview"):
        if job_type and experience_level and interview_format and focus_areas:
            st.session_state.questions = generate_initial_questions(job_type, experience_level, interview_format, focus_areas)
            st.session_state.current_question = 0
            st.session_state.responses = []
            st.session_state.current_response = ""
            st.session_state.recording = False
            st.session_state.total_feedback = []
            st.session_state.interview_started = True

    # Function to handle recording and feedback loop
    def handle_question():
        if st.session_state.current_question < len(st.session_state.questions):
            question = st.session_state.questions[st.session_state.current_question]
            st.write(f"Question {st.session_state.current_question + 1}: {question}")

            q = queue.Queue()
            if st.session_state.recording:
                st.write("Recording...")
                response_thread = threading.Thread(target=get_audio_response, args=(q,))
                response_thread.start()
                response_thread.join()
                if not q.empty():
                    st.session_state.current_response = q.get()
                st.session_state.recording = False  # Stop recording after getting response
            else:
                if st.button("Double click to Start Recording Your Answer", key=f"stop_recording_{st.session_state.current_question}"):
                    st.session_state.recording = True

            if st.session_state.current_response:
                st.write(f"Recorded Answer: {st.session_state.current_response}")
                feedback = get_feedback(st.session_state.current_response, st.session_state.questions[st.session_state.current_question])
                st.write(f"Feedback: {feedback}")

                # Calculate feedback score
                score = min(max(len(st.session_state.current_response.split()) // 5, 1), 10)
                st.session_state.total_feedback.append(score)

                followup_question = generate_followup_question(st.session_state.current_response)
                st.session_state.questions.append(followup_question)
                st.session_state.current_question += 1
                st.session_state.current_response = ""
                handle_question()  # Recursive call to handle the next question

    # Loop through questions and feedback until "Finish" is clicked
    if 'interview_started' in st.session_state and st.session_state.interview_started:
        handle_question()

    # Finish button to end the mock interview
    finish_button_placeholder = st.empty()
    if finish_button_placeholder.button("Finish"):
        st.write("Mock Interview Finished")
        st.session_state.current_question = len(st.session_state.questions)
        st.session_state.interview_started = False

        # Calculate total feedback score
        if st.session_state.total_feedback:
            total_score = sum(st.session_state.total_feedback) // len(st.session_state.total_feedback)
        else:
            total_score = 0

        if total_score >= 7:
            st.write(f"Overall Feedback Score: {total_score}/10")
            st.write("Great job! Keep it up!")
        elif 4 <= total_score < 7:
            st.write(f"Overall Feedback Score: {total_score}/10")
            st.write("Good effort! There are some areas to improve.")
        else:
            st.write(f"Overall Feedback Score: {total_score}/10")
            st.write("Needs improvement. Focus on the feedback provided.")
            
        # Center the "Finish" button
        finish_button_placeholder.markdown("""
            <style>
            div.stButton > button:first-child {
                margin: 0 auto;
                display: block;
            }
            </style>
        """, unsafe_allow_html=True)
        st.session_state.interview_started = False

# Main app logic
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.logged_in:
    home_page()
else:
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
