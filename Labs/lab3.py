import streamlit as st
from openai import OpenAI

def keep_last_n_user_turns(messages, n_user_turns=2, keep_first_assistant=True):

    if not messages:
        return messages

    preserved = []
    start_idx = 0
    if keep_first_assistant and messages[0]["role"] == "assistant":
        preserved = [messages[0]]
        start_idx = 1

    # Find indices of user messages
    user_idxs = [i for i in range(start_idx, len(messages)) if messages[i]["role"] == "user"]
    if len(user_idxs) <= n_user_turns:
        return preserved + messages[start_idx:]

    # Only keep last n user messages
    keep_user_idxs = set(user_idxs[-n_user_turns:])

    # Keep those user messages and the assistant message immediately after each (if any)
    kept = []
    i = start_idx
    while i < len(messages):
        if i in keep_user_idxs:
            kept.append(messages[i])  # user
            if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                kept.append(messages[i + 1])  # assistant response
            i += 2
        else:
            i += 1

    return preserved + kept



st.title("My Lab3 question answering chatbot")
openAI_Model = st.sidebar.selectbox("Which model?",
                                    ("mini", "regular"))
if openAI_Model == "mini":
    model_to_use = "gpt-4o-mini"
else:
    model_to_use = "gpt-4o-mini"


#create an OpenAI client
if 'client' not in st.session_state:
    api_key = st.secrets["OPENAI_KEY"]
    st.session_state.client = OpenAI(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state["messages"] = \
    [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    chat_msg = st.chat_message(msg["role"])
    chat_msg.write(msg["content"])

if prompt:= st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    client = st.session_state.client

    # Only send the last 2 user turns (conversation buffer)
    messages_for_llm = keep_last_n_user_turns(
        st.session_state.messages,
        n_user_turns=2
    )

    stream = client.chat.completions.create(
        model=model_to_use,
        messages=messages_for_llm,
        stream=True
    )

    
    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})

    st.session_state.messages = keep_last_n_user_turns(st.session_state.messages, n_user_turns=2)




