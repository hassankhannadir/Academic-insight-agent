"""Four-tab Streamlit application for academic insight and analytics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from academic_insight.agent import AcademicInsightAgent, AgentError, PriorTurn
from academic_insight.config import ConfigurationError, load_database_settings, load_groq_settings
from academic_insight.dashboard import load_dashboard_data, render_analytics, render_courses, render_students
from academic_insight.database import AcademicDatabase, DatabaseAccessError
from academic_insight.sql_guard import UnsafeQueryError


SUGGESTIONS = [
    "Who scored the highest marks in each course?",
    "Which students have attendance below 75%?",
    "What are the average marks in each course?",
    "Who are the top five performing students?",
]

st.set_page_config(page_title="Academic Insight", page_icon="🎓", layout="wide")
st.title("Academic Insight")
st.caption("Explore academic records and ask read-only questions.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "turns" not in st.session_state:
    st.session_state.turns = []

with st.sidebar:
    st.header("Conversation")
    if st.button("Clear chat", width="stretch"):
        st.session_state.messages = []
        st.session_state.turns = []
        st.rerun()
    st.caption("Agent queries return up to 100 rows and have a 3-second database time limit.")

ask_tab, students_tab, courses_tab, analytics_tab = st.tabs(
    ["Ask Academic Insight", "Students", "Courses", "Academic Analytics"]
)

with ask_tab:
    st.subheader("Ask Academic Insight")
    groq_settings = load_groq_settings()
    if not groq_settings.ready:
        st.info("Add your Groq API key and model name to .env.groq to enable questions.")

    if not st.session_state.messages:
        st.markdown("#### Try a question")
        columns = st.columns(2)
        suggestion = None
        for index, prompt in enumerate(SUGGESTIONS):
            with columns[index % 2]:
                if st.button(
                    prompt, key=f"suggestion_{index}", width="stretch",
                    disabled=not groq_settings.ready,
                ):
                    suggestion = prompt
    else:
        suggestion = None

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("rows"):
                st.dataframe(pd.DataFrame(message["rows"]), width="stretch", hide_index=True)

    typed = st.chat_input("Ask an academic question", disabled=not groq_settings.ready, max_chars=1000)
    question = suggestion or typed
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Checking academic records..."):
                try:
                    database = AcademicDatabase(load_database_settings())
                    agent = AcademicInsightAgent(database, groq_settings)
                    history = [PriorTurn(**turn) for turn in st.session_state.turns]
                    answer = agent.ask(question, history)
                    st.markdown(answer.text)
                    if answer.rows:
                        st.dataframe(pd.DataFrame(answer.rows), width="stretch", hide_index=True)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer.text, "rows": answer.rows}
                    )
                    st.session_state.turns.append({"question": question, "sql": answer.sql})
                except (ConfigurationError, AgentError, UnsafeQueryError, DatabaseAccessError) as exc:
                    message = str(exc)
                    st.error(message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": message, "rows": []}
                    )

dashboard_data = None
dashboard_error = None
with students_tab:
    try:
        with st.spinner("Loading academic records..."):
            dashboard_data = load_dashboard_data()
        render_students(dashboard_data)
    except (ConfigurationError, DatabaseAccessError) as exc:
        dashboard_error = str(exc)
        st.error(dashboard_error)

with courses_tab:
    if dashboard_error:
        st.error(dashboard_error)
    elif dashboard_data is not None:
        render_courses(dashboard_data)

with analytics_tab:
    if dashboard_error:
        st.error(dashboard_error)
    elif dashboard_data is not None:
        render_analytics(dashboard_data)
