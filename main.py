import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

st.set_page_config(page_title="Play with Excel",
                   page_icon='📊',
                   layout='wide')

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
    height: 150px !important;  /* adjust height */
    font-size: 1.3rem !important;
}
</style>
""", unsafe_allow_html=True)


st.subheader("Play with Excel")

# Hide the small text under uploader
st.markdown("""
<style>
.stFileUploader section div small {display: none;}
</style>
""", unsafe_allow_html=True)

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
    st.session_state.xlsx = None

# ---- Horizontal bar with uploader ----
col1, col2 = st.columns([2, 3])


with col1:
    file = st.file_uploader("    ",
                            type=["xlsx"],
                            on_change=on_change,
                            key="file_uploader")

# ---- Process file if uploaded ----
if file:
    try:
        data = pd.read_excel(file, sheet_name=0)
        st.session_state.xlsx = data.to_json(orient="records")
        st.success("Excel data extracted successfully!")
        st.dataframe(data.head())  # optional preview
    except Exception as e:
        st.error(f"Failed to process the Excel file: {e}")
else:
    st.session_state.xlsx = None

def generate_response(gemini_file, prompt_text):
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
        system_instruction=f"This is an uploaded Excel document data: {gemini_file}. "
                           f"If the question is about the document itself, summarize it (no column name lists)."
    )
    chat_session = model.start_chat(history=st.session_state.history)
    response = chat_session.send_message(prompt_text)
    return response

def initialize_session_state():
    if 'xlsx' not in st.session_state:
        st.session_state.xlsx = None
    if 'history' not in st.session_state:
        st.session_state.history = []

def update_ui():
    if st.session_state.xlsx is None:
        st.write('Please upload an Excel file to start chatting.')
    else:
        prompt = st.chat_input("Ask your question...")
        if prompt:
            st.session_state.history.append({"role": "user", "parts": [prompt]})
            with st.spinner("Thinking..."):
                response = generate_response(st.session_state.xlsx, prompt)
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
