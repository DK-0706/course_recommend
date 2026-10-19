"""Compatibility entry point for the student chat API."""
from rec_agent import run_course_agent


def chat_recommend(sid, message, history=None, shown_ids=None):
    """Run the LangGraph recommendation workflow for a chat turn."""
    return run_course_agent(sid, message, history, shown_ids)
