import streamlit as st
from openai import OpenAI
from pydantic import BaseModel


st.set_page_config(page_title="Lab 6 - Responses API Agent")
st.title("Lab 6: OpenAI Responses API Agent")
st.write("Ask a question, then ask a follow up. Web search is enabled for current information.")

client = OpenAI(api_key=st.secrets["OPENAI_KEY"])


if "last_response_id" not in st.session_state:
    st.session_state.last_response_id = None

if "first_answer" not in st.session_state:
    st.session_state.first_answer = ""

if "followup_answer" not in st.session_state:
    st.session_state.followup_answer = ""

st.sidebar.header("Options")
structured_mode = st.sidebar.checkbox("Return structured summary")
stream_mode = st.sidebar.checkbox("Stream response")


class ResearchSummary(BaseModel):
    main_answer: str
    key_facts: list[str]
    source_hint: str


user_question = st.text_input("Ask a question:")

if user_question:
    try:
       
        if structured_mode:
            response = client.responses.parse(
                model="gpt-4o",
                instructions="You are a helpful research assistant. Cite your sources when using web search.",
                input=user_question,
                tools=[{"type": "web_search_preview"}],
                text_format=ResearchSummary
            )

            parsed = response.output_parsed

            st.subheader("Answer")
            st.write(parsed.main_answer)

            st.subheader("Key Facts")
            for fact in parsed.key_facts:
                st.write(f"- {fact}")

            st.caption(parsed.source_hint)

            st.session_state.last_response_id = response.id
            st.session_state.first_answer = parsed.main_answer

        
        else:
            if stream_mode:
                stream = client.responses.create(
                    model="gpt-4o",
                    instructions="You are a helpful research assistant. Cite your sources when using web search.",
                    input=user_question,
                    tools=[{"type": "web_search_preview"}],
                    stream=True
                )

                full_text = ""
                placeholder = st.empty()

                final_response = None

                for event in stream:
                    # Stream text as it arrives
                    if getattr(event, "type", "") == "response.output_text.delta":
                        delta = event.delta
                        full_text += delta
                        placeholder.write(full_text)

                    # Capture final completed response object
                    elif getattr(event, "type", "") == "response.completed":
                        final_response = event.response

                if final_response is not None:
                    st.session_state.last_response_id = final_response.id
                st.session_state.first_answer = full_text

            else:
                response = client.responses.create(
                    model="gpt-4o",
                    instructions="You are a helpful research assistant. Cite your sources when using web search.",
                    input=user_question,
                    tools=[{"type": "web_search_preview"}]
                )

                st.write(response.output_text)
                st.session_state.last_response_id = response.id
                st.session_state.first_answer = response.output_text

    except Exception as e:
        st.error(f"Error: {e}")


st.divider()
follow_up = st.text_input("Ask a follow-up question:")

if follow_up:
    if st.session_state.last_response_id is None:
        st.warning("Please ask an initial question first.")
    else:
        try:
            response = client.responses.create(
                model="gpt-4o",
                instructions="You are a helpful research assistant. Cite your sources when using web search.",
                input=follow_up,
                tools=[{"type": "web_search_preview"}],
                previous_response_id=st.session_state.last_response_id
            )

            st.subheader("Follow-up Response")
            st.write(response.output_text)

            st.session_state.last_response_id = response.id
            st.session_state.followup_answer = response.output_text

        except Exception as e:
            st.error(f"Error: {e}")