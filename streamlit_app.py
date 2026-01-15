import streamlit as st
from openai import OpenAI, OpenAIError

st.title("MY Document question answering")
st.write(
    "Upload a document below and ask a question about it – GPT will answer! "
    "To use this app, you need to provide an OpenAI API key."
)

openai_api_key = st.text_input("OpenAI API Key", type="password")

client = None
api_key_valid = False

# Validate immediately
if openai_api_key:
    try:
        client = OpenAI(api_key=openai_api_key)
        client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
        )
        st.success("API key validated successfully ✅")
        api_key_valid = True
    except OpenAIError:
        st.error("Invalid API key (or model access issue). Please check and try again.")
        api_key_valid = False

if api_key_valid:
    uploaded_file = st.file_uploader("Upload a document (.txt or .md)", type=("txt", "md"))

    question = st.text_area(
        "Now ask a question about the document!",
        placeholder="Can you give me a short summary?",
        disabled=not uploaded_file,
    )

    if uploaded_file and question:
        document = uploaded_file.read().decode("utf-8", errors="ignore")

        messages = [{
            "role": "user",
            "content": f"Here's a document:\n{document}\n\n---\n\n{question}",
        }]

        stream = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            stream=True,
        )

        st.write_stream(stream)
