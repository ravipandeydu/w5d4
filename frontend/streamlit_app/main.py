import streamlit as st
import requests
import json
from pathlib import Path
import base64
from PIL import Image
import io

# Configure API endpoint
API_URL = "http://localhost:8000/api/v1"

def main():
    st.title("Notebook LLM Debug Interface")
    
    # Sidebar for file upload and settings
    with st.sidebar:
        st.header("Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "csv", "xlsx", "pptx", "html", "ipynb", "md", "png", "jpg"]
        )
        
        if uploaded_file:
            if st.button("Process Document"):
                with st.spinner("Processing document..."):
                    # Upload document
                    files = {"file": uploaded_file}
                    response = requests.post(f"{API_URL}/documents/upload/", files=files)
                    
                    if response.status_code == 200:
                        st.success("Document processed successfully!")
                        st.session_state.document_id = response.json()["document_id"]
                    else:
                        st.error(f"Error: {response.text}")
    
    # Main chat interface
    st.header("Chat Interface")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sources" in message:
                st.caption(f"Sources: {', '.join(message['sources'])}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Optional image upload for visual questions
        image_file = st.file_uploader("Upload an image for visual question", type=["png", "jpg", "jpeg"])
        image_data = None
        if image_file:
            image = Image.open(image_file)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            image_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Send query to API
        with st.spinner("Thinking..."):
            response = requests.post(
                f"{API_URL}/documents/query/",
                json={"query": prompt, "image_data": image_data}
            )
            
            if response.status_code == 200:
                result = response.json()
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"]
                })
            else:
                st.error(f"Error: {response.text}")
    
    # Debug information
    with st.expander("Debug Information"):
        if "document_id" in st.session_state:
            st.write(f"Current Document ID: {st.session_state.document_id}")
        st.write("API Endpoint:", API_URL)
        st.write("Number of Messages:", len(st.session_state.messages))

if __name__ == "__main__":
    main()
