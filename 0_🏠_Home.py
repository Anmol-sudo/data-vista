import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os

st.set_page_config(page_title="Data‑Vista", layout="wide")
st.title("Data‑Vista: Smart Notes Visualizer 🚀")

# Initialize Gemini
@st.cache_resource
def init_gemini():
    """Initialize Gemini with API key from environment or secrets"""
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY not found! Please set it in environment variables or .streamlit/secrets.toml")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash-latest')

model = init_gemini()

# Session state
for key, default in [
    ("text", ""), ("keywords", []), ("entities", []), ("topics", None),
    ("plots", {}), ("summaries", {"final": "", "partials": []})
]:
    st.session_state.setdefault(key, default)

st.markdown("""
### 🎯 Powered by Google Gemini AI
Upload your study notes in any format - typed documents, PDFs, or even handwritten notes!
Gemini's multimodal AI will intelligently extract and understand your content.
""")

def extract_with_gemini(uploaded_file) -> str:
    """Extract text from any document using Gemini's multimodal capabilities"""
    try:
        name = uploaded_file.name.lower()
        
        # For images (including handwritten notes)
        if name.endswith(('.png', '.jpg', '.jpeg')):
            img = Image.open(uploaded_file)
            st.image(img, caption="🖼️ Uploaded Image", use_container_width=True)
            
            with st.spinner("🤖 Gemini is reading your document..."):
                response = model.generate_content([
                    "Extract ALL text from this image. If it contains handwritten notes, transcribe them accurately. "
                    "Preserve the structure and formatting. Return only the extracted text without any additional commentary.",
                    img
                ])
                return response.text
        
        # For PDFs
        elif name.endswith('.pdf'):
            with st.spinner("🤖 Gemini is processing your PDF..."):
                # Upload file to Gemini File API
                uploaded_pdf = genai.upload_file(uploaded_file, mime_type="application/pdf")
                
                response = model.generate_content([
                    "Extract ALL text content from this PDF document. "
                    "Preserve the structure, headings, and important formatting. "
                    "If any pages have images with text, extract that too. "
                    "Return only the extracted text without commentary.",
                    uploaded_pdf
                ])
                
                # Clean up uploaded file
                genai.delete_file(uploaded_pdf.name)
                return response.text
        
        # For DOCX
        elif name.endswith('.docx'):
            with st.spinner("🤖 Gemini is processing your document..."):
                # Read DOCX as bytes and let Gemini handle it
                uploaded_file.seek(0)
                uploaded_doc = genai.upload_file(uploaded_file, mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                
                response = model.generate_content([
                    "Extract ALL text content from this DOCX document. "
                    "Preserve headings, paragraphs, and structure. "
                    "Return only the extracted text.",
                    uploaded_doc
                ])
                
                genai.delete_file(uploaded_doc.name)
                return response.text
        
        # For TXT files
        elif name.endswith('.txt'):
            raw = uploaded_file.read()
            for enc in ("utf-8", "utf-16", "latin-1"):
                try:
                    return raw.decode(enc)
                except Exception:
                    continue
            return ""
        
        else:
            st.error(f"Unsupported file type: {name}")
            return ""
            
    except Exception as e:
        st.error(f"❌ Error processing document: {str(e)}")
        st.info("💡 Tip: Make sure your GEMINI_API_KEY is valid and you haven't exceeded rate limits")
        return ""

# File uploader
uploaded = st.file_uploader(
    "📤 Upload notes (PDF, DOCX, TXT, PNG, JPG, JPEG)",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
    help="Supports typed documents, scanned pages, and handwritten notes"
)

if uploaded:
    with st.status("Processing document...", expanded=True) as status:
        st.write("📄 Reading file...")
        text = extract_with_gemini(uploaded)
        
        if text:
            st.session_state.text = text
            status.update(label="✅ Document processed successfully!", state="complete", expanded=False)
            
            # Show extraction stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Characters", f"{len(text):,}")
            with col2:
                st.metric("Words", f"{len(text.split()):,}")
            with col3:
                st.metric("Lines", f"{text.count(chr(10)) + 1:,}")
        else:
            status.update(label="❌ Failed to process document", state="error")

# Text preview
if st.session_state.text:
    st.subheader("📄 Extracted Text Preview")
    
    # Option to edit extracted text
    edited_text = st.text_area(
        "Review and edit if needed:",
        st.session_state.text,
        height=300,
        key="preview_text",
        help="You can edit the extracted text before analyzing"
    )
    
    if edited_text != st.session_state.text:
        if st.button("💾 Save Changes"):
            st.session_state.text = edited_text
            st.success("✅ Changes saved!")
    
    st.divider()
    
    st.info("""
    ### 🎯 Next Steps:
    Navigate to the sidebar pages to:
    - 📊 **Keyword Frequency**: See most common terms
    - ☁️ **Word Cloud**: Visualize important concepts  
    - 📈 **Topic Modeling**: Discover main themes
    - 🕸️ **Concept Graph**: Explore relationships
    - 📄 **Export Report**: Generate PDF with all insights
    """)
else:
    st.info("👆 Upload a document above to get started!")
    
    # Show example
    with st.expander("📖 What can Data-Vista do?"):
        st.markdown("""
        **Data-Vista** uses Google Gemini AI to transform your study notes into visual insights:
        
        ✅ **Accepts Multiple Formats**: PDF, Word docs, text files, images  
        ✅ **Reads Handwriting**: Gemini can transcribe handwritten notes  
        ✅ **Smart Extraction**: Understands document structure and context  
        ✅ **Visual Analysis**: Generates charts, word clouds, and concept maps  
        ✅ **Topic Discovery**: Automatically identifies main themes  
        ✅ **Export Reports**: Create professional PDFs with all visualizations  
        
        **Perfect for:**
        - Students reviewing lecture notes
        - Researchers analyzing papers
        - Anyone organizing knowledge from documents
        """)

# Footer
st.divider()
st.caption("Powered by Google Gemini 2.5 Flash • Built with Streamlit")
