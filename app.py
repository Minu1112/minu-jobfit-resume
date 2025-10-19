import os
import streamlit as st
from openai import OpenAI
from difflib import ndiff
from io import BytesIO
from fpdf import FPDF

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Minu's Jobfit Resume", page_icon="🧩", layout="wide")

# Load API key from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ==============================
# FUNCTIONS
# ==============================

def call_openai_chat(system_msg, prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1800,
    )
    return response.choices[0].message.content


def show_differences(original_text, modified_text):
    """Highlights differences between original and modified text."""
    diff = ndiff(original_text.splitlines(), modified_text.splitlines())
    html = ""
    for line in diff:
        if line.startswith("+ "):
            html += f"<span style='background-color:#d4edda;'>{line[2:]}</span><br>"
        elif line.startswith("- "):
            html += f"<span style='background-color:#f8d7da;text-decoration:line-through;'>{line[2:]}</span><br>"
        else:
            html += f"{line[2:]}<br>"
    return html


def make_pdf(resume_text, filename="Tailored_Resume.pdf"):
    """Converts tailored resume text to downloadable PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for line in resume_text.split("\n"):
        pdf.multi_cell(0, 8, line)
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer


# ==============================
# UI
# ==============================
st.title("🧩 Minu's Jobfit Resume App")
st.markdown("Upload your resume and job description to generate a **tailored resume and cover letter**!")

col1, col2 = st.columns(2)

with col1:
    resume_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
with col2:
    jd_file = st.file_uploader("Upload job description (PDF or DOCX)", type=["pdf", "docx"])

style_option = st.radio("Select Tailoring Intensity:", ["Light (keywords only)", "Full rewrite"])

if st.button("✨ Generate Tailored Resume"):
    if not resume_file or not jd_file:
        st.error("Please upload both files.")
    else:
        # For simplicity, read raw text from files
        import docx2txt
        import PyPDF2

        def extract_text(file):
            if file.name.endswith(".pdf"):
                reader = PyPDF2.PdfReader(file)
                return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif file.name.endswith(".docx"):
                return docx2txt.process(file)
            return ""

        resume_text = extract_text(resume_file)
        jd_text = extract_text(jd_file)

        if not resume_text or not jd_text:
            st.error("Could not extract text from one or both files.")
        else:
            system_msg = (
                "You are a professional resume editor. "
                "You will adjust tone, skills, and phrasing of the candidate’s resume to fit the job description."
            )

            if style_option == "Light (keywords only)":
                prompt = f"Match keywords and minor phrasing from this job description:\n\n{jd_text}\n\nResume:\n{resume_text}"
            else:
                prompt = f"Rewrite this resume to align with the following job description in a professional tone:\n\nJob Description:\n{jd_text}\n\nResume:\n{resume_text}"

            with st.spinner("Tailoring your resume..."):
                tailored_text = call_openai_chat(system_msg, prompt)

            st.subheader("📄 Tailored Resume")
            st.markdown(tailored_text)

            # Highlight changes
            with st.expander("🔍 View differences (highlighted)"):
                st.markdown(show_differences(resume_text, tailored_text), unsafe_allow_html=True)

            # Download PDF
            pdf_buffer = make_pdf(tailored_text)
            st.download_button(
                label="⬇️ Download Tailored Resume (PDF)",
                data=pdf_buffer,
                file_name="Tailored_Resume.pdf",
                mime="application/pdf"
            )

            # Cover Letter
            if st.button("💌 Generate Cover Letter"):
                cover_prompt = f"Write a short, personalized cover letter for this job based on the tailored resume and job description:\n\nJob Description:\n{jd_text}\n\nResume:\n{tailored_text}"
                with st.spinner("Generating your cover letter..."):
                    cover_letter = call_openai_chat("You are a professional HR writer.", cover_prompt)
                st.subheader("💌 Cover Letter")
                st.markdown(cover_letter)
                pdf_buffer2 = make_pdf(cover_letter, "Cover_Letter.pdf")
                st.download_button(
                    label="⬇️ Download Cover Letter (PDF)",
                    data=pdf_buffer2,
                    file_name="Cover_Letter.pdf",
                    mime="application/pdf"
                )

