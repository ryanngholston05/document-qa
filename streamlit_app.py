import streamlit as st
from openai import OpenAI, OpenAIError

# App title and description
st.title("My Document Question Answering App")
st.write(
    "Upload a document and ask a question about it. "
    "Your OpenAI API key will be validated immediately."
)

# API key input
openai_api_key = st.text_input("OpenAI API Key", type="password")

client = None
api_key_valid = False

# ✅ A. Validate API key immediately
if openai_api_key:
    try:
        client = OpenAI(api_key=openai_api_key)

        # Lightweight test call to validate the key
        client.chat.completions.create(
            model="gpt-5-nano",  # test model
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
        )

        st.success("API key validated successfully ✅")
        api_key_valid = True

    except OpenAIError as e:
        st.error("Invalid API key. Please check and try again.")
        api_key_valid = False

# Only continue if API key is valid
if api_key_valid:

    uploaded_file = st.file_uploader(
        "Upload a document (.txt or .md)", type=("txt", "md")
    )

    question = st.text_area(
        "Ask a question about the document",
        placeholder="Can you give me a short summary?",
        disabled=not uploaded_file,
    )

    if uploaded_file and question:
        document = uploaded_file.read().decode("utf-8")

        messages = [
            {
                "role": "user",
                "content": f"Here is the document:\n{document}\n\n---\n\n{question}",
            }
        ]

        # ✅ B. Change the model here
        stream = client.chat.completions.create(
            model="gpt-5-nano",  # ← change this if needed
            messages=messages,
            stream=True,
        )

        st.write_stream(stream)
