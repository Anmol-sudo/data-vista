import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
import io
import os
import pdfplumber
import json

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
    # Use gemini-1.5-flash for better free tier support
    return genai.GenerativeModel('gemini-2.0-flash')

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

def log_to_console(message: str, data: str = ""):
    """Log messages to browser console for debugging"""
    try:
        # Escape and truncate data for safe JSON embedding
        safe_data = data.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")[:500]
        
        js_code = f"""
        <script>
        console.log("[Data-Vista] {message}");
        console.log("[Data-Vista] Response preview:", "{safe_data}...");
        console.log("[Data-Vista] Full length:", {len(data)} + " characters");
        </script>
        """
        components.html(js_code, height=0)
    except Exception as e:
        # Silent fail - don't break app if logging fails
        pass

def get_pdf_page_count(pdf_file) -> int:
    """Get total page count of PDF"""
    try:
        pdf_file.seek(0)
        with pdfplumber.open(pdf_file) as pdf:
            return len(pdf.pages)
    except Exception:
        return 0

def extract_pdf_pages_as_images(pdf_file, start_page: int, end_page: int):
    """Extract specific pages from PDF as images for Gemini"""
    try:
        pdf_file.seek(0)
        images = []
        
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            start = max(0, start_page - 1)  # Convert to 0-indexed
            end = min(total_pages, end_page)
            
            for page_num in range(start, end):
                page = pdf.pages[page_num]
                # Convert page to image
                img = page.to_image(resolution=150)
                pil_img = img.original
                images.append(pil_img)
        
        return images
    except Exception as e:
        st.error(f"Error extracting PDF pages: {str(e)}")
        return []

def extract_with_gemini(uploaded_file, start_page=None, end_page=None) -> str:
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
                log_to_console("Image processed", response.text)
                return response.text
        
        # For PDFs with page selection
        elif name.endswith('.pdf'):
            pdf_file = io.BytesIO(uploaded_file.read())
            total_pages = get_pdf_page_count(pdf_file)
            
            if total_pages == 0:
                st.error("Could not read PDF file")
                return ""
            
            # Use provided page range or default to all pages
            start = start_page if start_page else 1
            end = end_page if end_page else total_pages
            
            with st.spinner(f"🤖 Gemini is processing pages {start}-{end} of your PDF..."):
                # Extract pages as images
                page_images = extract_pdf_pages_as_images(pdf_file, start, end)
                
                if not page_images:
                    return ""
                
                # Process each page with Gemini
                all_text = []
                progress_bar = st.progress(0)
                
                for idx, img in enumerate(page_images):
                    page_num = start + idx
                    st.write(f"📄 Processing page {page_num}...")
                    
                    response = model.generate_content([
                        f"Extract ALL text from this PDF page (page {page_num}). "
                        "Preserve structure, headings, and formatting. "
                        "If there are tables, preserve their structure. "
                        "Return only the extracted text.",
                        img
                    ])
                    
                    log_to_console(f"PDF page {page_num} processed", response.text)
                    all_text.append(f"\n--- Page {page_num} ---\n{response.text}")
                    progress_bar.progress((idx + 1) / len(page_images))
                
                progress_bar.empty()
                return "\n".join(all_text)
        
        # For DOCX
        elif name.endswith('.docx'):
            with st.spinner("🤖 Gemini is processing your document..."):
                uploaded_file.seek(0)
                uploaded_doc = genai.upload_file(uploaded_file, mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                
                response = model.generate_content([
                    "Extract ALL text content from this DOCX document. "
                    "Preserve headings, paragraphs, and structure. "
                    "Return only the extracted text.",
                    uploaded_doc
                ])
                
                log_to_console("DOCX processed", response.text)
                genai.delete_file(uploaded_doc.name)
                return response.text
        
        # For TXT files
        elif name.endswith('.txt'):
            uploaded_file.seek(0)
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

# Page selection for PDFs
start_page = None
end_page = None

if uploaded and uploaded.name.lower().endswith('.pdf'):
    # Get page count
    pdf_bytes = io.BytesIO(uploaded.read())
    total_pages = get_pdf_page_count(pdf_bytes)
    uploaded.seek(0)  # Reset for later processing
    
    if total_pages > 0:
        st.info(f"📄 PDF has {total_pages} pages")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            start_page = st.number_input(
                "Start page",
                min_value=1,
                max_value=total_pages,
                value=1,
                help="First page to process"
            )
        
        with col2:
            end_page = st.number_input(
                "End page",
                min_value=1,
                max_value=total_pages,
                value=min(10, total_pages),  # Default to first 10 pages
                help="Last page to process (max recommended: 20 pages)"
            )
        
        with col3:
            st.metric("Pages", f"{end_page - start_page + 1}")
        
        if end_page < start_page:
            st.warning("⚠️ End page must be >= start page")
        elif (end_page - start_page + 1) > 20:
            st.warning("⚠️ Processing more than 20 pages may hit rate limits. Consider splitting into smaller batches.")

# Process button
if uploaded:
    if st.button("🚀 Process Document", type="primary", use_container_width=True):
        with st.status("Processing document...", expanded=True) as status:
            st.write("📄 Reading file...")
            text = extract_with_gemini(uploaded, start_page, end_page)
            
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
        ✅ **Page Selection**: Choose specific pages to process (saves API quota!)  
        ✅ **Visual Analysis**: Generates charts, word clouds, and concept maps  
        ✅ **Topic Discovery**: Automatically identifies main themes  
        ✅ **Export Reports**: Create professional PDFs with all visualizations  
        
        **Perfect for:**
        - Students reviewing lecture notes
        - Researchers analyzing papers
        - Anyone organizing knowledge from documents
        
        **💡 Pro Tip**: For large PDFs, process 10-20 pages at a time to avoid rate limits!
        """)

# Footer
st.divider()
st.caption("Powered by Google Gemini 1.5 Flash • Built with Streamlit • Check browser console (F12) for AI response logs")
