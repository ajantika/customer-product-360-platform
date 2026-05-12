"""Groq + Llama 3.1 wrapper. Single entrypoint used by Customer 360 and Product 360."""
import os

import streamlit as st

try:
    from groq import Groq
except ImportError:
    Groq = None


MODEL = "llama-3.1-8b-instant"


def _api_key() -> str | None:
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return os.environ.get("GROQ_API_KEY")


def _format_context(context: dict) -> str:
    """Stringify a context dict into compact key:value lines for the system prompt."""
    lines = []
    for k, v in context.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v[:20]:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def ask_about(context: dict, question: str) -> str:
    """Answer a question grounded in the provided context dict.

    Context examples:
      Customer 360: {"customer": "OpenAI", "region": "NAMER", "mrr": 24500,
                     "products": ["API Gateway: 130%", "CDN: 45%"], ...}
      Product 360:  {"product": "API Gateway", "adoption_pct": 62.5,
                     "top_customers": [...], "regions": [...]}
    """
    api_key = _api_key()
    if not api_key:
        return "GROQ_API_KEY is not configured. Add it to .streamlit/secrets.toml or your environment."
    if Groq is None:
        return "groq package is not installed. Run: pip install groq"

    client = Groq(api_key=api_key)
    system = (
        "You are an analytics assistant for a SaaS Customer & Product 360 platform. "
        "Answer the user's question using ONLY the context below. Be concise (2-4 sentences) "
        "and quantitative — cite specific numbers from the context. If the context is insufficient, say so.\n\n"
        f"CONTEXT:\n{_format_context(context)}"
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            temperature=0.2,
            max_tokens=400,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"LLM error: {e}"
