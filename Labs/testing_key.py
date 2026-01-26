import streamlit as st

st.title("My App Using Secrets")

secret_key = st.secrets.API_KEY
st.write("Here's my secret key:", secret_key)

st.write("And here again:", st.secrets["API_KEY"])

