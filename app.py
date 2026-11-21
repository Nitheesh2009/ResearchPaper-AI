
import streamlit as st
from dotenv import load_dotenv
import os
import fitz
import requests

load_dotenv(override=True)

st.set_page_config(
    page_title="ResearchPaper AI",
    page_icon="📚",
    layout="wide"
)

st.title("ResearchPaper AI")
st.subheader("Your AI-powered Research Paper Assistant")

st.write(
    "Upload a research paper and ask questions "
    "about its contents."
)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

if api_key:
    st.success("Gemini API key detected.")
else:
    st.error("Gemini API key not found. Check your .env file.")

st.divider()
st.header("Upload Research Paper")

uploaded_file = st.file_uploader(
    "Choose your research paper",
    type=["pdf"]
)

if uploaded_file is not None:
    try:
        pdf_document = fitz.open(
            stream=uploaded_file.getvalue(),
            filetype="pdf"
        )

        extracted_pages = []

        for page_number, page in enumerate(pdf_document):
            extracted_pages.append(
                f"\n--- Page {page_number + 1} ---\n"
                + page.get_text()
            )

        total_pages = len(pdf_document)
        pdf_document.close()

        extracted_text = "\n".join(extracted_pages)

        st.success(
            f"PDF uploaded successfully! Total pages: {total_pages}"
        )

        if extracted_text.strip():

            with st.expander("View extracted PDF text"):
                st.text_area(
                    "PDF Content",
                    extracted_text,
                    height=250
                )

            st.divider()
            st.header("Ask Your Research Paper")

            question = st.text_input(
                "Enter your question",
                placeholder="What is the main objective of this research?"
            )

            if st.button("Generate Answer", type="primary"):

                if not api_key:
                    st.error("Gemini API key is missing.")

                elif not question.strip():
                    st.warning("Please enter a question.")

                else:
                    prompt = f"""
You are an academic research paper assistant.

Answer using ONLY the research paper below.

Rules:
1. Do not invent information.
2. If the answer is unavailable, say so.
3. Include page references whenever possible.
4. Give clear and structured answers.

RESEARCH PAPER:
{extracted_text[:30000]}

QUESTION:
{question}
"""

                    url = (
                        "https://generativelanguage.googleapis.com/"
                        "v1beta/interactions"
                    )

                    headers = {
                        "Content-Type": "application/json",
                        "x-goog-api-key": api_key
                    }

                    payload = {
                        "model": "gemini-3.5-flash-lite",
                        "input": prompt
                    }

                    with st.spinner(
                        "Gemini is analyzing your research paper..."
                    ):
                        try:
                            response = requests.post(
                                url,
                                headers=headers,
                                json=payload,
                                timeout=120
                            )

                            if response.status_code == 200:
                                result = response.json()

                                answer = result.get("output_text", "")

                                if not answer:
                                    for step in result.get("steps", []):
                                        if step.get("type") == "model_output":
                                            for item in step.get("content", []):
                                                if item.get("type") == "text":
                                                    answer += item.get("text", "")

                                if answer:
                                    st.subheader("AI Answer")
                                    st.markdown(answer)
                                    st.caption("Powered by Gemini 3.5 Flash")
                                else:
                                    st.error(
                                        "The API responded, but no answer text was found."
                                    )

                            else:
                                st.error(
                                    f"Gemini API Error: {response.status_code}"
                                )
                                st.code(response.text[:2000])

                        except requests.exceptions.Timeout:
                            st.error(
                                "Gemini request timed out. Please try again."
                            )

                        except requests.exceptions.RequestException as error:
                            st.error(f"Connection error: {error}")

        else:
            st.warning("No readable text found in this PDF.")

    except Exception as error:
        st.error(f"PDF processing failed: {error}")
