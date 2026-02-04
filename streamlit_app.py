import streamlit as st

st.set_page_config(page_title="Labs", page_icon="🧪", layout="centered")

def home():
    st.title("Ryann's IST488 Lab Work")
    st.write("Welcome! Use sidebar to navigate labs")
# Pages
home_page = st.Page(home, title="Home", default=True)
lab1_page  = st.Page("Labs/lab1.py", title="Lab 1")
lab2_page  = st.Page("Labs/lab2.py", title="Lab 2")
lab3_page  = st.Page("Labs/lab3.py", title="Lab 3")

# Navigation
pg = st.navigation([home_page, lab1_page, lab2_page, lab3_page])
pg.run()




# import streamlit as st
# from openai import OpenAI

# # Show title and description.
# st.title("Lab 2")
# st.write(
#     "Upload a document below and ask a question about it – GPT will answer! "
# )

# # Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# # via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management


# try:
#     openai_api_key = st.secrets["API_KEY"]
# except KeyError:
#     st.error("OpenAI API key not found in Streamlit secrets.", icon="❌")
#     st.stop()


# try:
#     # Create OpenAI client using secret key
#     client = OpenAI(api_key=openai_api_key)

#     # Validate API key
#     client.models.list()
#     st.success("API key loaded from secrets and validated!", icon="✅")

#     # File uploader
#     uploaded_file = st.file_uploader(
#         "Upload a document (.txt or .md)", type=("txt", "md")
#     )

#     # Question input
#     question = st.text_area(
#         "Now ask a question about the document!",
#         placeholder="Can you give me a short summary?",
#         disabled=not uploaded_file,
#     )

#     if uploaded_file and question:
#         document = uploaded_file.read().decode()

#         messages = [
#             {
#                 "role": "user",
#                 "content": f"Here's a document:\n{document}\n\n---\n\n{question}",
#             }
#         ]

#         # Stream response
#         stream = client.chat.completions.create(
#             model="gpt-5-nano",
#             messages=messages,
#             stream=True,
#         )

#         st.write_stream(stream)

# except Exception as e:
#     st.error(f"Error connecting to OpenAI: {str(e)}", icon="❌")