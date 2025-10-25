import streamlit as st
from textblob import TextBlob
import spacy

st.set_page_config(layout="wide")
st.title("🧠 NLP Analysis")

if not st.session_state.text:
    st.warning("Please upload text on Home."); st.stop()

nlp = spacy.load("en_core_web_sm")

if st.button("Run Analysis"):
    sentiment = TextBlob(st.session_state.text).sentiment
    st.write(f"Polarity: {sentiment.polarity:.2f}")
    st.write(f"Subjectivity: {sentiment.subjectivity:.2f}")
    doc = nlp(st.session_state.text)
    ents = [(e.text, e.label_) for e in doc.ents][:50]
    st.session_state.entities = ents
    st.write("Named Entities (first 50):")
    st.write(ents)
