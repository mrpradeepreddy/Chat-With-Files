import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
import fitz  # PyMuPDF for PDF text extraction

load_dotenv()

st.set_page_config(page_title="Play with Documents",
                   page_icon='📊',
                   layout='wide')

# --- CSS to make uploader full width ---
st.markdown("""
<style>
/* outermost container of uploader */
div[data-testid="stFileUploader"] {
    width: 100% !important;
    max-width: 100% !important;
}

/* section inside uploader */
div[data-testid="stFileUploader"] > section {
    width: 100% !important;
    max-width: 100% !important;
}

/* inner drop area */
div[data-testid="stFileUploader"] > section > div {
    width: 100% !important;
    max-width: 100% !important;
}

/* optional: taller and larger text */
div[data-testid="stFileUploader"] > section > div > div {
    height: 100px
    width:100px !important;  /* adjust height */
    font-size: 1.3rem !important;
}
</style>
""", unsafe_allow_html=True)

st.subheader("Play with Documents")

# Hide the small text under uploader
st.markdown("""
<style>
.stFileUploader section div small {display: none;}
</style>
""", unsafe_allow_html=True)

# --- Gemini API config ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

def on_change():
    st.session_state.history = []
    st.session_state.file_content = None

# ---- Horizontal bar with uploader ----
col1, col2 = st.columns([2, 3])

with col1:
    file = st.file_uploader(
        label="",
        type=["xlsx", "xls", "csv", "pdf"],  # accept these types
        on_change=on_change,
        key="file_uploader"
    )

# ---- Process file if uploaded ----
if file:
    try:
        filename = file.name.lower()
        if filename.endswith((".xlsx", ".xls")):
            data = pd.read_excel(file)
            st.session_state.file_content = data.to_json(orient="records")
            st.success("Excel data extracted successfully!")
            st.dataframe(data.head())
        elif filename.endswith(".csv"):
            data = pd.read_csv(file)
            st.session_state.file_content = data.to_json(orient="records")
            st.success("CSV data extracted successfully!")
            st.dataframe(data.head())
        elif filename.endswith(".pdf"):
            doc = fitz.open(stream=file.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            st.session_state.file_content = text
            st.success("PDF text extracted successfully!")
            st.text_area("Extracted Text Preview", text[:2000] + "...")
        else:
            st.error("Unsupported file type.")
    except Exception as e:
        st.error(f"Failed to process the file: {e}")
else:
    st.session_state.file_content = None

def generate_response(file_content, prompt_text):
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
        system_instruction=f"This is an uploaded document data: {file_content}. "
                           f"If the question is about the document itself, summarize it (no column name lists)."
    )
    chat_session = model.start_chat(history=st.session_state.history)
    response = chat_session.send_message(prompt_text)
    return response

def initialize_session_state():
    if 'file_content' not in st.session_state:
        st.session_state.file_content = None
    if 'history' not in st.session_state:
        st.session_state.history = []

def update_ui():
    if st.session_state.file_content is None:
        st.write('Please upload a file to start chatting.')
    else:
        prompt = st.chat_input("Ask your question...")
        if prompt:
            st.session_state.history.append({"role": "user", "parts": [prompt]})
            with st.spinner("Thinking..."):
                response = generate_response(st.session_state.file_content, prompt)
            st.session_state.history.append({"role": "model", "parts": [response.text]})

    # Display chat history
    for item in st.session_state.history:
        role = 'assistant' if item['role'] == 'model' else 'user'
        with st.chat_message(role):
            st.markdown(item['parts'][0])

def main():
    initialize_session_state()
    update_ui()

if __name__ == "__main__":
    main()
