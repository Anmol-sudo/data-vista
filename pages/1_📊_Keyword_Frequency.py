import streamlit as st
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import re

st.set_page_config(page_title="Keyword Frequency — Data‑Vista", layout="wide")
st.title("📊 Keyword Frequency")

def basic_clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", text)
    return text.strip()

STOPWORDS = set("""
a an the and or but if then else for while of to from in on at by with without within over under into out up down
is are was were be been being have has had do does did as that this these those it its itself themselves himself herself
you your yours we our ours they their theirs he him she her i me my mine not no nor so such than too very can could
should would will just also more most some any each other about above after again against all am between both before
during further here there when where why how only own same until once
""".split())

WORD_RE = re.compile(r"[A-Za-z](?:[A-Za-z'-]*[A-Za-z])?")

def tokenize(text: str):
    try:
        tokens = [m.group(0).lower() for m in WORD_RE.finditer(text)]
    except re.error:
        tokens = re.split(r"[^A-Za-z]+", text.lower())
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 2]

@st.cache_data
def get_keywords_cached(txt: str):
    return tokenize(basic_clean(txt))

if not st.session_state.get("text"):
    st.warning("Please upload text on Home.")
    st.stop()

keywords = st.session_state.get("keywords") or get_keywords_cached(st.session_state.text)
st.session_state.keywords = keywords

if not keywords:
    st.info("No keywords detected.")
    st.stop()

word_freq = Counter(keywords).most_common(25)
df = pd.DataFrame(word_freq, columns=["Keyword", "Frequency"]).sort_values("Frequency")

fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
ax.barh(df["Keyword"], df["Frequency"], color="#74a9ff")
ax.set_xlabel("Frequency")
ax.set_ylabel("Keyword")
ax.set_title("Top 25 Keywords")
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
plt.tight_layout()

st.pyplot(fig, use_container_width=True)

path = "keyword_freq.png"
fig.savefig(path, bbox_inches="tight", dpi=220)
if "plots" not in st.session_state:
    st.session_state.plots = {}
st.session_state.plots["keyword_freq"] = path
st.caption("Saved chart for PDF (Matplotlib).")
