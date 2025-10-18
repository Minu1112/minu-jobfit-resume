import os
import io
import re
import tempfile
import streamlit as st
from pathlib import Path

# Allow secret-managed OPENAI key on Streamlit Cloud or local .streamlit/secrets.toml
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Parsing libraries (pdfplumber, docx2txt)
try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import docx2txt
except Exception:
    docx2txt = None

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# OpenAI
try:
    import openai
except Exception:
    openai = None

# --------------------- Helpers ---------------------
def extract_text_from_pdf(file_bytes):
    if pdfplumber is None:
        raise RuntimeError("pdfplumber required. Install pdfplumber.")
    text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)

def extract_text_from_docx(file_bytes):
    if docx2txt is None:
        raise RuntimeError("docx2txt required. Install docx2txt.")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.write(file_bytes)
    tmp.flush()
    tmp.close()
    try:
        text = docx2txt.process(tmp.name) or ""
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
    return text

def extract_text_from_upload(uploaded_file):
    data = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith('.pdf'):
        return extract_text_from_pdf(data)
    if name.endswith('.docx') or name.endswith('.doc'):
        return extract_text_from_docx(data)
    return data.decode('utf-8', errors='ignore')

def build_prompt_for_openai(resume_text, jd_text, level='light', cover_letter=False):
    if cover_letter:
        system = ("You are a professional career coach. Write a concise, persuasive cover letter that highlights why the candidate is a good fit for the job. Use the resume and job description as context.")
        prompt = f"Job Description:\n{jd_text}\n\nResume:\n{resume_text}\n\nWrite a professional cover letter (max 300 words)."
        return system, prompt

    if level == 'light':
        system = ("You are an expert resume writer. Adjust only lightly: match keywords from the JD and make minimal wording updates. Do not rewrite entire bullets.")
    else:
        system = ("You are an expert resume writer. Rewrite bullets for strong alignment to the JD while preserving facts.")

    prompt = f"Job Description:\n{jd_text}\n\nOriginal Resume:\n{resume_text}\n\nReturn the tailored resume text."
    return system, prompt

def call_openai_chat(system_msg, user_msg):
    if openai is None:
        raise RuntimeError('openai package missing. Install openai.')
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('Please set OPENAI_API_KEY environment variable or add it to Streamlit secrets.')
    openai.api_key = key
    # Use ChatCompletion (this code assumes openai package compatibility)
    response = openai.ChatCompletion.create(
        model='gpt-4o-mini' if hasattr(openai, 'ChatCompletion') else 'gpt-4o-mini',
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        temperature=0.2,
        max_tokens=1800,
    )
    return response['choices'][0]['message']['content'].strip()

def highlight_differences(original, tailored):
    import difflib
    diff = difflib.ndiff(original.split(), tailored.split())
    html = []
    for token in diff:
        if token.startswith('-'):
            html.append(f'<span style="background-color:#ffefef;border-radius:3px;padding:1px;margin:1px;">{token[2:]}</span> ')
        elif token.startswith('+'):
            html.append(f'<span style="background-color:#eaffea;border-radius:3px;padding:1px;margin:1px;">{token[2:]}</span> ')
        else:
            html.append(token[2:] + ' ')
    return ''.join(html)

def make_pretty_pdf(text, filename):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=filename)
    styles = getSampleStyleSheet()
    body = []
    para_style = ParagraphStyle('resume', parent=styles['Normal'], fontSize=10, leading=13, spaceAfter=6)
    for para in text.split('\n\n'):
        body.append(Paragraph(para.replace('\n', ' '), para_style))
        body.append(Spacer(1, 8))
    doc.build(body)
    buffer.seek(0)
    return buffer

# --------------------- Streamlit UI ---------------------
st.set_page_config(page_title="Minu's Jobfit Resume", layout='wide')
st.title("Minu's Jobfit Resume ✨")
st.caption("Upload your resume & job description, and get a tailored resume + optional cover letter.")

col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=['pdf', 'docx', 'doc', 'txt'])
with col2:
    jd_file = st.file_uploader("Upload job description (PDF, DOCX, or TXT)", type=['pdf', 'docx', 'doc', 'txt'])

level = st.radio("Tailoring level", ['Light (keyword adjust)', 'Deep (rewrite bullets)'])
include_cover = st.checkbox("Also generate a cover letter")

if st.button('Generate Tailored Resume'):
    if not resume_file or not jd_file:
        st.error('Please upload both resume and job description.')
    else:
        with st.spinner('Processing...'):
            resume_text = extract_text_from_upload(resume_file)
            jd_text = extract_text_from_upload(jd_file)

        lvl = 'light' if level.startswith('Light') else 'deep'
        system_msg, prompt = build_prompt_for_openai(resume_text, jd_text, level=lvl)
        tailored_text = call_openai_chat(system_msg, prompt)

        st.success('Tailored resume generated!')

        # Side-by-side comparison
        st.subheader('🧾 Side-by-Side Resume Comparison')
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Original Resume")
            st.text_area('Original', resume_text, height=400)
        with c2:
            st.markdown("### Tailored Resume")
            st.text_area('Tailored', tailored_text, height=400)

        # Diff highlighting
        st.subheader('🔍 Highlighted Differences')
        html_diff = highlight_differences(resume_text, tailored_text)
        st.markdown(html_diff, unsafe_allow_html=True)

        # Download outputs
        pdf_buf = make_pretty_pdf(tailored_text, 'Tailored_Resume.pdf')
        st.download_button('📄 Download Tailored Resume (PDF)', pdf_buf, file_name='Minu_Jobfit_Tailored.pdf')

        # Optional cover letter
        if include_cover:
            st.divider()
            st.subheader('💌 Generated Cover Letter')
            sys_c, pr_c = build_prompt_for_openai(resume_text, jd_text, level=lvl, cover_letter=True)
            cover_text = call_openai_chat(sys_c, pr_c)
            st.text_area('Cover Letter', cover_text, height=300)
            cover_pdf = make_pretty_pdf(cover_text, 'Cover_Letter.pdf')
            st.download_button('📎 Download Cover Letter (PDF)', cover_pdf, file_name='Minu_Jobfit_CoverLetter.pdf')

st.markdown('---')
st.markdown('**Notes:** This version adds a side-by-side resume comparison view, highlighted differences, optional cover letter generation, and formatted PDF downloads for a polished, professional experience.')