import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter
import re

st.set_page_config(layout="wide")
st.title("🗺️ Concept Graph (Mind Map)")

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
    st.warning("Please upload text on Home."); st.stop()

keywords = st.session_state.keywords or get_keywords(st.session_state.text)
topics = st.session_state.topics

def build_concept_graph(keywords, topics):
    G = nx.Graph()
    freq = Counter(keywords).most_common(25)
    for w,c in freq: G.add_node(w, size=10+c, type="keyword")
    window=8
    for i in range(len(keywords)-window):
        s=set(keywords[i:i+window]); L=list(s)
        for a in range(len(L)):
            for b in range(a+1,len(L)):
                u,v=L[a],L[b]
                if G.has_edge(u,v): G[u][v]["weight"] += 1
                else: G.add_edge(u,v,weight=1)
    if topics:
        for t_idx, terms in enumerate(topics["topic_terms"]):
            hub=f"Topic {t_idx+1}"
            w=float(topics["topic_weights"][t_idx]); G.add_node(hub, size=20+int(100*w), type="topic")
            for term in terms[:5]:
                if term not in G: G.add_node(term, size=12, type="term")
                G.add_edge(hub, term, weight=2)
    return G

G = build_concept_graph(keywords, topics)
pos = nx.spring_layout(G, k=0.35, iterations=50, seed=42)
sizes=[G.nodes[n].get("size",10)*30 for n in G.nodes]
colors=[]
for n in G.nodes:
    t=G.nodes[n].get("type","keyword")
    colors.append("#ff7f0e" if t=="topic" else "#1f77b4" if t=="term" else "#2ca02c")
plt.figure(figsize=(10,6))
nx.draw_networkx_nodes(G,pos,node_size=sizes,node_color=colors,alpha=0.85,linewidths=0.5,edgecolors="#333")
widths=[0.5+0.3*G[u][v]["weight"] for u,v in G.edges]
nx.draw_networkx_edges(G,pos,width=widths,alpha=0.3,edge_color="#555")
labels={n:n for n in G.nodes if G.nodes[n].get("size",10)>=18 or G.nodes[n].get("type")=="topic"}
nx.draw_networkx_labels(G,pos,labels=labels,font_size=9)
plt.axis("off")
st.pyplot(plt.gcf())
path="concept_graph.png"
plt.savefig(path, bbox_inches="tight", dpi=200)
st.session_state.plots["concept_graph"]=path
plt.close()
