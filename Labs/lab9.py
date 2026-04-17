
import os
import json
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor


st.title("Lab 09: Multi-Agent Trip Planner")
st.write(
    """
    This app uses a supervisor agent that coordinates three specialist agents:
    - Research Agent — looks up destination highlights, culture, tips, and weather
    - Budget Agent — estimates total trip costs based on your budget level
    - Itinerary Agent — builds a day-by-day schedule based on your interests

    The supervisor decides which agents to call and in what order, then synthesizes
    their outputs into a complete travel plan.
    """
)


os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


agent_llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
supervisor_llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'travel_data.json'), 'r') as f:
    TRAVEL_DATA = json.load(f)



@tool
def search_destination(query: str) -> str:
    """Look up travel information about a destination including highlights,
    best time to visit, culture, tips, and weather."""
    # Match query against city names (case-insensitive)
    query_lower = query.lower()
    destinations = TRAVEL_DATA["destinations"]

    for city, data in destinations.items():
        if city in query_lower:
            result = {
                "destination": city.title(),
                "highlights": data["highlights"],
                "best_time": data["best_time"],
                "culture": data["culture"],
                "tips": data["tips"],
                "weather": data["weather"]
            }
            return json.dumps(result)

    # Generic fallback if no city matched
    fallback = {
        "destination": query,
        "highlights": "A wonderful destination with many things to explore.",
        "best_time": "Spring and fall are generally pleasant times to visit.",
        "culture": "Rich local culture with unique traditions and cuisine.",
        "tips": "Research local customs before you go and keep an open mind.",
        "weather": "Weather varies by season — check a forecast closer to your trip."
    }
    return json.dumps(fallback)


@tool
def calculate_budget(destination: str, days: int, budget_level: str) -> str:
    """Estimate total trip costs for a destination given the number of days
    and budget level (budget, moderate, or luxury)."""
    budget_level_lower = budget_level.lower()
    daily_costs = TRAVEL_DATA["daily_costs"]
    flight_estimates = TRAVEL_DATA["flight_estimates"]

    # Get daily cost breakdown, default to moderate if level not found
    if budget_level_lower not in daily_costs:
        budget_level_lower = "moderate"
    costs = daily_costs[budget_level_lower]

    # Calculate daily total and trip total (excluding flights)
    daily_total = sum(costs.values())
    trip_total = daily_total * days

    # Get flight cost
    dest_lower = destination.lower()
    flight_cost = flight_estimates.get(dest_lower, flight_estimates.get("default", 700))

    # Grand total
    grand_total = trip_total + flight_cost

    # Money saving tips
    saving_tips = TRAVEL_DATA["money_saving_tips"]

    result = {
        "destination": destination,
        "days": days,
        "budget_level": budget_level_lower,
        "daily_breakdown": costs,
        "daily_total": daily_total,
        "trip_subtotal": trip_total,
        "estimated_flight": flight_cost,
        "grand_total": grand_total,
        "money_saving_tips": saving_tips
    }
    return json.dumps(result)


@tool
def create_schedule(destination: str, days: int, interests: str) -> str:
    """Build a day-by-day itinerary for a destination based on the traveler's interests."""
    activities_pool = TRAVEL_DATA["activities"]

    # Parse interests string into a list
    interest_list = [i.strip().lower() for i in interests.split(",")]

    # Collect matching activities from the pool
    matched_activities = []
    for interest in interest_list:
        for category, activity_list in activities_pool.items():
            if interest in category or category in interest:
                matched_activities.extend(activity_list)

    # If no matches, use all activities as fallback
    if not matched_activities:
        for activity_list in activities_pool.values():
            matched_activities.extend(activity_list)

    # Remove duplicates while preserving order
    seen = set()
    unique_activities = []
    for a in matched_activities:
        if a not in seen:
            seen.add(a)
            unique_activities.append(a)

    # Build day-by-day schedule with morning/afternoon/evening slots
    schedule = {}
    activity_index = 0
    total_activities = len(unique_activities)

    for day in range(1, days + 1):
        schedule[f"Day {day}"] = {
            "morning": unique_activities[activity_index % total_activities],
            "afternoon": unique_activities[(activity_index + 1) % total_activities],
            "evening": unique_activities[(activity_index + 2) % total_activities]
        }
        activity_index += 3

    result = {
        "destination": destination,
        "days": days,
        "interests": interests,
        "itinerary": schedule
    }
    return json.dumps(result)




research_agent = create_react_agent(
    model=agent_llm,
    tools=[search_destination],
    name='research_agent',
    prompt=(
        'You are a travel research specialist. '
        'When asked about any destination, you ALWAYS use the search_destination tool '
        'to look up accurate information. Never make up destination details.'
    )
)

budget_agent = create_react_agent(
    model=agent_llm,
    tools=[calculate_budget],
    name='budget_agent',
    prompt=(
        'You are a travel budget specialist. '
        'When asked to estimate costs for a trip, you ALWAYS use the calculate_budget tool. '
        'Never invent cost figures — always rely on the tool.'
    )
)

itinerary_agent = create_react_agent(
    model=agent_llm,
    tools=[create_schedule],
    name='itinerary_agent',
    prompt=(
        'You are a travel itinerary specialist. '
        'When asked to create a schedule or day-by-day plan, you ALWAYS use the create_schedule tool. '
        'Never invent activities — always rely on the tool.'
    )
)


# Part 3: Creating the Supervisor
 
workflow = create_supervisor(
    agents=[research_agent, budget_agent, itinerary_agent],
    model=supervisor_llm,
    prompt=(
        'You are a travel planning supervisor coordinating three specialist agents:\n'
        '  - research_agent: looks up destination highlights, culture, tips, and weather\n'
        '  - budget_agent: estimates trip costs based on destination, days, and budget level\n'
        '  - itinerary_agent: builds a day-by-day schedule based on destination, days, and interests\n\n'
        'Routing rules:\n'
        '  - Questions about a destination (what to see, culture, weather, tips) → research_agent\n'
        '  - Questions about cost or budget → budget_agent\n'
        '  - Questions about schedule or itinerary → itinerary_agent\n'
        '  - Full trip planning requests → call ALL THREE agents\n\n'
        'After all agents have responded, synthesize their outputs into one organized, '
        'well-structured travel plan. Do not leave out any agent\'s findings.'
    )
)
 
# Compile the workflow into a runnable app
multi_agent_app = workflow.compile()
 
 


with st.sidebar:
    st.header(" Trip Settings")
 
    destination = st.text_input("Destination", value="Paris")
    days = st.slider("Trip Duration (days)", min_value=1, max_value=14, value=5)
    budget_level = st.selectbox("Budget Level", ["Budget", "Moderate", "Luxury"])
    interests = st.multiselect(
        "Interests",
        options=["Food", "History", "Art", "Nature", "Nightlife", "Shopping"],
        default=["Food", "History"]
    )
 
# --- Step 4B: Session State ---
if 'ma_result' not in st.session_state:
    st.session_state.ma_result = None
if 'ma_messages' not in st.session_state:
    st.session_state.ma_messages = None
 
# --- Step 4C: Query Construction & Invocation ---
interests_str = ", ".join(interests) if interests else "Food, History"
 
trip_query = (
    f"Plan a {days}-day trip to {destination}. "
    f"My budget level is {budget_level.lower()}. "
    f"My interests include: {interests_str}. "
    f"Please provide destination research, a budget breakdown, and a day-by-day itinerary."
)
 
st.subheader("Your Trip Query")
st.info(trip_query)
 
if st.button("Plan My Trip", type="primary"):
    with st.spinner("Agents are collaborating on your trip plan..."):
        result = multi_agent_app.invoke({
            'messages': [{'role': 'user', 'content': trip_query}]
        })
        st.session_state.ma_result = result['messages'][-1].content
        st.session_state.ma_messages = result['messages']
 
# Display result
if st.session_state.ma_result:
    st.subheader(" Your Multi-Agent Trip Plan")
    st.markdown(st.session_state.ma_result)
 
    with st.sidebar:
        st.markdown("---")
        st.subheader("Agent Activity Log")
        agent_emojis = {
            'research_agent': '🔍',
            'budget_agent': '💰',
            'itinerary_agent': '🗓️',
        }
        for msg in st.session_state.ma_messages:
            msg_name = getattr(msg, 'name', None)
            tool_calls = getattr(msg, 'tool_calls', None)
            if msg_name and msg_name in agent_emojis:
                emoji = agent_emojis[msg_name]
                st.write(f"{emoji} **{msg_name}** was called")
                if tool_calls:
                    for tc in tool_calls:
                        tool_name = tc.get('name', '') if isinstance(tc, dict) else getattr(tc, 'name', '')
                        st.caption(f"  └─ tool: `{tool_name}`")
 
 
 
st.divider()
st.subheader("Experiment: Single Agent vs Multi-Agent")
st.write(
    "Compare the multi-agent output above with a single LLM that has no tools. "
    "Notice differences in data quality, structure, and specificity."
)
 
if st.button(" Run Single-Agent Comparison"):
    with st.spinner("Running single-agent response..."):
        single_llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
        single_result = single_llm.invoke(trip_query)
        st.subheader("Single-Agent Response (No Tools)")
        st.markdown(single_result.content)
 

st.divider()
st.subheader("Chatbot Mode (MessagesState & StateGraph)")
st.write(
    "This chatbot uses a hand-built **StateGraph** with `MessagesState`. "
    "The supervisor routes each message to the right specialist agent, "
    "then a synthesizer produces the final response."
)
 
# 6A

def supervisor_node(state: MessagesState):
    """Reads the conversation and outputs a routing decision word."""
    messages = state['messages']
    routing_prompt = (
        "You are a router. Read the user's latest message and reply with exactly one word:\n"
        "- 'research'   → if they ask about a destination (highlights, culture, weather, tips)\n"
        "- 'budget'     → if they ask about cost, price, or budget\n"
        "- 'itinerary'  → if they ask for a schedule or day-by-day plan\n"
        "- 'all'        → if they want a full trip plan covering all three topics\n"
        "- 'chat'       → for greetings, thanks, or anything else\n\n"
        "Reply with ONE word only."
    )
    response = supervisor_llm.invoke(
        [{"role": "system", "content": routing_prompt}] + 
        [{"role": m.type if hasattr(m, 'type') else 'user', "content": m.content} for m in messages]
    )
    return {'messages': [response]}
 
 
def research_node(state: MessagesState):
    """Invokes the research_agent to look up destination info."""
    messages = state['messages']
    # Find the original user message (skip the routing decision)
    user_messages = [m for m in messages if getattr(m, 'type', '') == 'human']
    query = user_messages[-1].content if user_messages else messages[0].content
    result = research_agent.invoke({'messages': [{'role': 'user', 'content': query}]})
    response_content = result['messages'][-1].content
    return {'messages': [{"role": "assistant", "content": response_content}]}
 
 
def budget_node(state: MessagesState):
    """Invokes the budget_agent to estimate trip costs."""
    messages = state['messages']
    user_messages = [m for m in messages if getattr(m, 'type', '') == 'human']
    query = user_messages[-1].content if user_messages else messages[0].content
    result = budget_agent.invoke({'messages': [{'role': 'user', 'content': query}]})
    response_content = result['messages'][-1].content
    return {'messages': [{"role": "assistant", "content": response_content}]}
 
 
def itinerary_node(state: MessagesState):
    """Invokes the itinerary_agent to build a day-by-day schedule."""
    messages = state['messages']
    user_messages = [m for m in messages if getattr(m, 'type', '') == 'human']
    query = user_messages[-1].content if user_messages else messages[0].content
    result = itinerary_agent.invoke({'messages': [{'role': 'user', 'content': query}]})
    response_content = result['messages'][-1].content
    return {'messages': [{"role": "assistant", "content": response_content}]}
 
 
def run_all_agents(state: MessagesState):
    """Sequentially invokes all three agents and combines their outputs."""
    messages = state['messages']
    user_messages = [m for m in messages if getattr(m, 'type', '') == 'human']
    query = user_messages[-1].content if user_messages else messages[0].content
 
    research_result = research_agent.invoke({'messages': [{'role': 'user', 'content': query}]})
    budget_result = budget_agent.invoke({'messages': [{'role': 'user', 'content': query}]})
    itinerary_result = itinerary_agent.invoke({'messages': [{'role': 'user', 'content': query}]})
 
    combined = (
        "### 🔍 Research Agent\n" + research_result['messages'][-1].content + "\n\n" +
        "### 💰 Budget Agent\n" + budget_result['messages'][-1].content + "\n\n" +
        "### 🗓️ Itinerary Agent\n" + itinerary_result['messages'][-1].content
    )
    return {'messages': [{"role": "assistant", "content": combined}]}
 
 
def synthesizer_node(state: MessagesState):
    """Produces a final well-organized response from all agent outputs."""
    messages = state['messages']
    synth_prompt = (
        "You are a travel planning assistant. Based on the conversation so far, "
        "provide a helpful, friendly, and well-organized response. "
        "If agent data is available, summarize it clearly. "
        "If it's just a greeting or general chat, respond conversationally."
    )
    response = supervisor_llm.invoke(
        [{"role": "system", "content": synth_prompt}] +
        [{"role": m.type if hasattr(m, 'type') else 'user', "content": m.content} for m in messages]
    )
    return {'messages': [response]}
 
 
# 6B: 
def route_from_supervisor(state: MessagesState):
    last_msg = state['messages'][-1].content.strip().lower()
    if 'research' in last_msg:
        return 'research'
    elif 'budget' in last_msg:
        return 'budget'
    elif 'itinerary' in last_msg:
        return 'itinerary'
    elif 'all' in last_msg:
        return 'all'
    else:
        return 'chat'
 
 
#6C
 
chatbot_graph = StateGraph(MessagesState)
 
# Add nodes
chatbot_graph.add_node('supervisor', supervisor_node)
chatbot_graph.add_node('research', research_node)
chatbot_graph.add_node('budget', budget_node)
chatbot_graph.add_node('itinerary', itinerary_node)
chatbot_graph.add_node('all_agents', run_all_agents)
chatbot_graph.add_node('synthesizer', synthesizer_node)
 
# Add edges
chatbot_graph.add_edge(START, 'supervisor')
chatbot_graph.add_conditional_edges(
    'supervisor',
    route_from_supervisor,
    {
        'research': 'research',
        'budget': 'budget',
        'itinerary': 'itinerary',
        'all': 'all_agents',
        'chat': 'synthesizer',
    },
)
chatbot_graph.add_edge('research', 'synthesizer')
chatbot_graph.add_edge('budget', 'synthesizer')
chatbot_graph.add_edge('itinerary', 'synthesizer')
chatbot_graph.add_edge('all_agents', 'synthesizer')
chatbot_graph.add_edge('synthesizer', END)
 
chatbot_app = chatbot_graph.compile()
 
 
#6D: 
 
# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
 
# Display existing chat history
for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
 
# Handle new user input
if user_input := st.chat_input("Ask me about a destination, budget, itinerary, or full trip plan..."):
    # Display and store user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
 
    # Invoke the chatbot graph
    with st.chat_message("assistant"):
        with st.spinner("Routing to the right agent..."):
            chat_result = chatbot_app.invoke({
                'messages': [{'role': 'user', 'content': user_input}]
            })
            response = chat_result['messages'][-1].content
            st.markdown(response)
 
    st.session_state.chat_history.append({"role": "assistant", "content": response})