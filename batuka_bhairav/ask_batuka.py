from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

ACTIVE_MARKET = os.getenv("MARKET", "IN").upper()


def load_dashboard(market: str = ACTIVE_MARKET) -> dict:
    path = Path(f"docs/data/{market}.json")
    if not path.exists():
        raise FileNotFoundError(
            f"Dashboard JSON not found at {path}. Run the engine first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def find_stock_record(payload: dict, query: str) -> Optional[dict]:
    records = payload.get("explainability", [])
    q = query.strip().lower()

    # direct symbol match
    for rec in records:
        if rec.get("symbol", "").lower() == q:
            return rec

    # name/symbol contains
    for rec in records:
        symbol = rec.get("symbol", "").lower()
        name = rec.get("name", "").lower()
        if q in symbol or q in name:
            return rec

    # heuristic for question like: "Why did BHEL score 83?"
    tokens = re.findall(r"[A-Za-z0-9&.-]+", q)
    for token in tokens:
        for rec in records:
            if token == rec.get("symbol", "").lower():
                return rec

    return None


def build_stock_explanation_prompt(question: str, stock_record: dict, payload: dict) -> str:
    return f"""
You are Batuka, a stock intelligence assistant.

Answer the user's question in plain English, with a finance-friendly but simple tone.
Use only the provided structured data. Do not invent facts.
If the score in the user's question differs slightly from the actual stored score, politely correct it.

USER QUESTION:
{question}

MARKET CONTEXT:
- Market: {payload.get("market_name")}
- Regime: {payload.get("regime")}
- News Sentiment: {payload.get("news_sentiment")}
- Generated At: {payload.get("generated_at")}

STOCK RECORD:
{json.dumps(stock_record, indent=2)}

INSTRUCTIONS:
1. Explain why the stock got its conviction score.
2. Mention momentum, volume, technicals, regime, sector, and news input.
3. Keep it concise but useful.
4. End with a 1-line takeaway.
""".strip()


def call_llm(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are Batuka, a practical market intelligence assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()

    elif provider == "groq":
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": "You are Batuka, a practical market intelligence assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()

    else:
        raise ValueError("Unsupported LLM_PROVIDER. Use 'groq' or 'openai'.")


def answer_batuka_question(question: str, market: str = ACTIVE_MARKET) -> str:
    payload = load_dashboard(market)
    rec = find_stock_record(payload, question)

    if rec:
        prompt = build_stock_explanation_prompt(question, rec, payload)
        return call_llm(prompt)

    # fallback answer without stock match
    btst = payload.get("btst_cards", [])[:5]
    intraday = payload.get("intraday_cards", [])[:5]
    longterm = payload.get("longterm_cards", [])[:5]

    summary = {
        "market_name": payload.get("market_name"),
        "regime": payload.get("regime"),
        "top_btst": btst,
        "top_intraday": intraday,
        "top_longterm": longterm,
        "sector_table": payload.get("sector_table", [])[:5],
        "news_drivers": payload.get("news_drivers", [])[:5],
    }

    prompt = f"""
You are Batuka, a stock intelligence assistant.

The user asked:
{question}

No exact stock match was found in the explainability records.
Use the summary below and answer helpfully.
If needed, say the exact symbol was not found and suggest the user ask with the stock symbol.

SUMMARY:
{json.dumps(summary, indent=2)}
""".strip()

    return call_llm(prompt)
