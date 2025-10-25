import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re

st.set_page_config(layout="wide")
st.title("☁️ Word Cloud")

def basic_clean(text):
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

def tokenize(text):
    tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def get_keywords(txt):
    return tokenize(basic_clean(txt))

if not st.session_state.text:
    st.warning("Please upload text on Home.")
    st.stop()

keywords = st.session_state.keywords or get_keywords(st.session_state.text)
if keywords:
    wc = WordCloud(width=1200, height=500, background_color="white", collocations=False).generate(" ".join(keywords))
    fig, ax = plt.subplots(figsize=(12,5))
    ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
    st.pyplot(fig)
    path = "word_cloud.png"
    fig.savefig(path, bbox_inches="tight", dpi=200)
    st.session_state.plots["word_cloud"] = path
else:
    st.info("No keywords available.")
