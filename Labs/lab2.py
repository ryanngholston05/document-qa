import streamlit as st
from openai import OpenAI


# Show title and description.
st.title("Lab 2")
st.write(
    "Upload a document below and ask a question about it – GPT will answer! "
)


st.sidebar.header("Summary Options")

summary_style = st.sidebar.radio(
    "Choose a summary format:",
    (
        "100 words",
        "2 connecting paragraphs",
        "5 bullet points",
    ),
)

# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management


try:
    openai_api_key = st.secrets["API_KEY"]
except KeyError:
    st.error("OpenAI API key not found in Streamlit secrets.", icon="❌")
    st.stop()


try:
    # Create OpenAI client using secret key
    client = OpenAI(api_key=openai_api_key)

    # Validate API key
    client.models.list()
    st.success("API key loaded from secrets and validated!", icon="✅")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a document (.txt or .md)", type=("txt", "md")
    )

    # Question input
    question = st.text_area(
        "Now ask a question about the document!",
        placeholder="Can you give me a short summary?",
        disabled=not uploaded_file,
    )

    if uploaded_file and question:
        document = uploaded_file.read().decode()

        messages = [
            {
                "role": "user",
                "content": f"Here's a document:\n{document}\n\n---\n\n{question}",
            }
        ]

        # Stream response
        stream = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            stream=True,
        )

        st.write_stream(stream)

except Exception as e:
    st.error(f"Error connecting to OpenAI: {str(e)}", icon="❌")