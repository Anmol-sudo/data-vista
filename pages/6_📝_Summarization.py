import streamlit as st
from transformers import pipeline
import re

st.set_page_config(page_title="Summarization — Data‑Vista", layout="wide")
st.title("📝 Summarization")

@st.cache_resource
def get_summarizer(model_name="sshleifer/distilbart-cnn-12-6"):
    # Cached so we don’t reload weights on each run
    return pipeline("summarization", model=model_name)

def safe_chunks(txt, max_chars=120_000, chunk_size=2800, overlap=300, max_chunks=8):
    # Bound input size and number of chunks for Cloud CPU stability
    txt = txt[:max_chars]
    chunks=[]; i=0
    while i < len(txt) and len(chunks) < max_chunks:
        chunks.append(txt[i:i+chunk_size])
        i += chunk_size - overlap
    return chunks

if "summaries" not in st.session_state:
    st.session_state.summaries = {"final": "", "partials": []}

if not st.session_state.get("text"):
    st.warning("Please upload text on Home."); st.stop()

# Controls
model_name = st.selectbox(
    "Summarizer model",
    ["sshleifer/distilbart-cnn-12-6", "facebook/bart-large-cnn"],
    index=0
)
max_len = st.slider("Max summary length (tokens approx.)", 60, 300, 150, 10)

# Action
if st.button("Generate Summary"):
    text = st.session_state.text.strip()
    if len(text) <= 200:
        st.warning("Text is too short to summarize.")
    else:
        try:
            summarizer = get_summarizer(model_name)
        except Exception as e:
            summarizer = None
            st.warning(f"Model load failed; using fallback. {e}")

        if summarizer:
            chunks = safe_chunks(text)
            partial=[]; prog=st.progress(0)
            for i,ch in enumerate(chunks,1):
                res = summarizer(
                    ch,
                    max_length=max_len,
                    min_length=max(30, max_len//3),
                    do_sample=False,
                    truncation=True
                )
                partial.append(res[0]["summary_text"])
                prog.progress(int(i/len(chunks)*100))
                st.caption(f"Chunk {i}/{len(chunks)} summarized.")
            combined=" ".join(partial)
            if len(chunks) > 1:
                res2 = summarizer(
                    combined,
                    max_length=max_len,
                    min_length=max(30, max_len//3),
                    do_sample=False,
                    truncation=True
                )
                final = res2[0]["summary_text"]
            else:
                final = combined
            st.session_state.summaries = {"final": final, "partials": partial}
        else:
            # Fast extractive fallback
            sents = re.split(r"(?<=[.!?])\s+", text)
            final = " ".join(sents[:5])
            st.session_state.summaries = {"final": final, "partials": []}

# Full summary display (always reflects what goes to PDF)
if st.session_state.summaries.get("final"):
    st.write("**Summary (full):**")
    st.text_area(
        "Summary (full)",
        value=st.session_state.summaries["final"],
        height=420,
        key="full_summary_area"
    )
    with st.expander("Show summary as paragraph", expanded=False):
        st.write(st.session_state.summaries["final"])
    st.download_button(
        "Download summary.txt",
        st.session_state.summaries["final"],
        file_name="summary.txt"
    )
else:
    st.info("Click Generate Summary to produce a summary for the uploaded text.")
