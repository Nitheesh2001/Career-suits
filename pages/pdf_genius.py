import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import json  # Add this import statement
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from utils.auth import authenticate_user, register_user

# Load environment variables
load_dotenv()

# Set the API key for Google Generative AI
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details. If the answer is not in
    provided context, just say, "answer is not available in the context", don't provide the wrong answer.\n\n
    Context:\n {context}\n
    Question: \n{question}\n
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    st.write("Reply: ", response["output_text"])

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    else:
        return {}

def show_login_page():
    st.title("Welcome to PDFGenius!")
    st.subheader("Log in to effortlessly analyze and interact with your PDF documents. Unlock insights and streamline your workflow!")

    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()
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

def show_signup_page():
    st.title("Signup")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Signup"):
        if password == confirm_password:
            users = load_users()
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
    st.set_page_config(page_title="Chat PDF")
    st.header("Chat with PDF using PDFGenius💁")

    st.subheader("Upload your PDF Files")
    pdf_docs = st.file_uploader("Attach your PDF files here:", accept_multiple_files=True)
    if st.button("Submit & Process"):
        if pdf_docs:
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.session_state["pdf_processed"] = True
                st.success("PDF files processed and vector store updated.")
        else:
            st.warning("Please upload PDF files before processing.")

    if "pdf_processed" in st.session_state and st.session_state["pdf_processed"]:
        st.subheader("Ask a Question from the PDF Files")
        user_question = st.text_input("Enter your question here:")
        if st.button("Submit Question"):
            if user_question:
                user_input(user_question)
            else:
                st.warning("Please enter a question.")

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "login"
    if "pdf_processed" not in st.session_state:
        st.session_state["pdf_processed"] = False

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
