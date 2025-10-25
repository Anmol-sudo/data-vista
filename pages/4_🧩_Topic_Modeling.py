import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from sklearn.preprocessing import normalize
from scipy import sparse
import re
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🧩 Topic Modeling")

def topic_model(text, n_topics=5, max_features=5000):
    def basic_clean(s):
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", s)
        return s.strip()
    docs = re.split(r"(?<=[.!?])\s+", basic_clean(text))
    docs = [d for d in docs if len(d.split()) >= 5]
    if len(docs) < 3: return None
    vec = TfidfVectorizer(max_features=max_features, stop_words="english")
    nmf = NMF(n_components=min(n_topics, max(2, len(docs)//2)), random_state=42, init="nndsvda", max_iter=400)
    X = vec.fit_transform(docs)
    if X.shape[0] < 2 or X.shape[1] < 2: return None
    W = nmf.fit_transform(X); H = nmf.components_; feats = vec.get_feature_names_out()
    topic_terms = [[feats[i] for i in comp.argsort()[::-1][:8]] for comp in H]
    doc_topic = normalize(W, norm="l1", axis=1)
    if sparse.issparse(doc_topic): weights = doc_topic.mean(axis=0).A1
    else: weights = doc_topic.mean(axis=0).reshape(-1)
    weights = weights/(weights.sum()+1e-12)
    return {"topic_terms":topic_terms, "topic_weights":weights}

if not st.session_state.text:
    st.warning("Please upload text on Home."); st.stop()

k = st.slider("Number of topics", 2, 8, 5)
if st.button("Detect Topics"):
    topics = topic_model(st.session_state.text, k)
    if not topics:
        st.warning("Not enough content.")
    else:
        st.session_state.topics = topics
        labels = [f"Topic {i+1}: " + ", ".join(t[:4]) for i,t in enumerate(topics["topic_terms"])]
        df = pd.DataFrame({"Topic": labels, "Weight": topics["topic_weights"]})
        fig = px.pie(df, values="Weight", names="Topic", title="Topic Distribution")
        st.plotly_chart(fig, use_container_width=True)
        try:
            path = "topic_pie.png"; fig.write_image(path, scale=2); st.session_state.plots["topic_pie"]=path
        except Exception as e:
            st.caption(f"(Could not save topic image: {e})")
        for i, terms in enumerate(topics["topic_terms"]):
            st.write(f"• Topic {i+1} → {', '.join(terms[:8])}")
