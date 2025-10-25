import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib import utils
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap
import os
import unicodedata
import re
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📄 Export Report (PDF)")

if not st.session_state.get("text"):
    st.warning("Please upload text on Home."); st.stop()

colA, colB, colC = st.columns([1,1,1])
with colA:
    max_summary_chars = st.number_input("Max summary characters in PDF", 200, 4000, 800, 50)
with colB:
    image_scale = st.slider("Image scale (for saved charts)", 1, 4, 3, 1)
with colC:
    add_headers = st.checkbox("Add headers/footers", value=True)
use_unicode_font = st.checkbox("Use Unicode font (fix missing glyphs)", value=True)

if use_unicode_font:
    try:
        if not os.path.exists("fonts"):
            os.makedirs("fonts", exist_ok=True)
        pdfmetrics.registerFont(TTFont("DejaVuSans", "fonts/DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "fonts/DejaVuSans-Bold.ttf"))
        FONT_BODY = "DejaVuSans"
        FONT_BOLD = "DejaVuSans-Bold"
    except Exception:
        FONT_BODY = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"
else:
    FONT_BODY = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

PAGE_SIZE = A4
W, H = PAGE_SIZE
MARGIN_L = 2.0 * cm
MARGIN_R = 2.0 * cm
MARGIN_T = 1.8 * cm
MARGIN_B = 1.6 * cm
CONTENT_W = W - (MARGIN_L + MARGIN_R)

H1 = (FONT_BOLD, 16)
H2 = (FONT_BOLD, 12)
BODY = (FONT_BODY, 10)
LINE = 14

GAP_AFTER_H1 = 14
GAP_AFTER_H2 = 10
GAP_AFTER_PARAGRAPH = 8
GAP_AFTER_IMAGE = 14
TOP_OFFSET = 0.8 * cm
FOOT_CLEAR = 1.2 * cm

def sanitize_for_pdf(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\u00A0", " ")
    s = (s.replace("\u2013", "-")
           .replace("\u2014", "-")
           .replace("\u2018", "'")
           .replace("\u2019", "'")
           .replace("\u201C", '"')
           .replace("\u201D", '"')
           .replace("\u2022", "•"))
    s = re.sub(r"[^\x09\x0A\x0D\x20-\x7E•]", " ", s)
    return s

def header_footer(c, page_num):
    if not add_headers:
        return
    c.setStrokeColorRGB(0.8,0.8,0.8)
    c.setLineWidth(0.3)
    c.line(MARGIN_L, H - MARGIN_T + 0.6*cm, W - MARGIN_R, H - MARGIN_T + 0.6*cm)
    c.setFont(FONT_BOLD, 9)
    c.drawString(MARGIN_L, H - MARGIN_T + 0.75*cm, "Data‑Vista Report")
    c.setFont(FONT_BODY, 9)
    c.drawRightString(W - MARGIN_R, H - MARGIN_T + 0.75*cm, datetime.now().strftime("%Y-%m-%d %H:%M"))
    c.setFont(FONT_BODY, 9)
    c.drawRightString(W - MARGIN_R, MARGIN_B - 0.9*cm, f"Page {page_num}")

def new_page(c, page_num):
    if page_num > 0:
        c.showPage()
    page_num += 1
    header_footer(c, page_num)
    y = H - MARGIN_T - TOP_OFFSET
    return page_num, y

def draw_h1(c, text, y):
    c.setFont(*H1); c.drawString(MARGIN_L, y, sanitize_for_pdf(text))
    return y - GAP_AFTER_H1 - LINE

def draw_h2(c, text, y):
    c.setFont(*H2); c.drawString(MARGIN_L, y, sanitize_for_pdf(text))
    return y - GAP_AFTER_H2 - int(LINE * 0.6)

def draw_body(c, text, y, max_width=CONTENT_W):
    c.setFont(*BODY)
    wrap = textwrap.wrap(sanitize_for_pdf(text), width=int(max_width/6))
    for line in wrap:
        if y < MARGIN_B + FOOT_CLEAR:
            return None, True
        c.drawString(MARGIN_L, y, line)
        y -= LINE
    return y - GAP_AFTER_PARAGRAPH, False

def draw_image(c, path, y, max_w=CONTENT_W, max_h=10*cm):
    try:
        img = utils.ImageReader(path)
        iw, ih = img.getSize()
        scale = min(max_w/iw, max_h/ih, 1.0)
        w, h = iw*scale, ih*scale
        if y - h < MARGIN_B + FOOT_CLEAR:
            return None, True
        c.drawImage(ImageReader(path), MARGIN_L, y - h, width=w, height=h, preserveAspectRatio=True, mask='auto')
        return y - h - GAP_AFTER_IMAGE, False
    except Exception:
        return y, False

def section_image(c, title, key, y, page, max_h):
    if key not in st.session_state.plots:
        return page, y
    path = st.session_state.plots[key]
    if not os.path.exists(path):
        return page, y

    title_drawn = False
    def ensure_title(_y):
        nonlocal title_drawn
        if not title_drawn:
            title_drawn = True
            return draw_h2(c, title, _y)
        return _y

    y = ensure_title(y)
    y2, page_break = draw_image(c, path, y, max_w=CONTENT_W, max_h=max_h)

    if page_break:
        page, y = new_page(c, page)
        y = ensure_title(y)
        y2, _ = draw_image(c, path, y, max_w=CONTENT_W, max_h=max_h)

    y = (y2 if y2 is not None else y)
    return page, y

filename = "Data-Vista-Report.pdf"
if st.button("Generate PDF"):
    c = canvas.Canvas(filename, pagesize=PAGE_SIZE)
    c.setTitle("Data‑Vista Report")

    page, y = new_page(c, 0)
    y = draw_h1(c, "Data‑Vista: Visual Summary Report", y)

    pdf_summary = st.session_state.summaries.get("final", "")
    if pdf_summary:
        if len(pdf_summary) > max_summary_chars:
            pdf_summary = pdf_summary[:max_summary_chars].rsplit(" ", 1)[0] + " ..."
        y = draw_h2(c, "Summary", y)
        y, br = draw_body(c, pdf_summary, y)
        if br:
            page, y = new_page(c, page)

    if st.session_state.entities:
        ents = ", ".join([f"{t} ({l})" for t,l in st.session_state.entities[:40]])
        y = draw_h2(c, "Named Entities (sample)", y)
        y, br = draw_body(c, ents, y)
        if br:
            page, y = new_page(c, page)

    page, y = section_image(c, "Keyword Frequency", "keyword_freq", y, page, max_h=9*cm)
    page, y = section_image(c, "Word Cloud", "word_cloud", y, page, max_h=9*cm)
    page, y = section_image(c, "Topic Distribution", "topic_pie", y, page, max_h=9*cm)
    page, y = section_image(c, "Concept Graph", "concept_graph", y, page, max_h=11*cm)

    c.showPage(); c.save()
    with open(filename, "rb") as f:
        st.download_button("Download PDF", f, file_name=filename, mime="application/pdf")
    st.success("Report generated.")
