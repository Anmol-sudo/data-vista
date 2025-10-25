import os
import subprocess
import sys
import streamlit as st

@st.cache_resource
def ensure_spacy_model(model_name: str = "en_core_web_sm"):
    try:
        import spacy
        spacy.load(model_name)
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
        except Exception as e:
            st.warning(f"Could not auto-download spaCy model {model_name}: {e}")

@st.cache_resource
def load_summarizer():
    try:
        from transformers import pipeline
        return pipeline("summarization", model="facebook/bart-large-cnn")
    except Exception:
        return None
