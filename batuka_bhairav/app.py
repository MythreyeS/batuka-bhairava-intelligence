from __future__ import annotations

import os
import gradio as gr
from batuka_bhairav.ask_batuka import answer_batuka_question

DEFAULT_MARKET = os.getenv("MARKET", "IN").upper()


def chat_fn(message, history, market):
    try:
        answer = answer_batuka_question(message, market=market)
        return answer
    except Exception as e:
        return f"Error: {str(e)}"


with gr.Blocks(title="Ask Batuka Why") as demo:
    gr.Markdown("# Ask Batuka Why")
    gr.Markdown("Ask questions like: `Why did BHEL score 83?` or `Show me top BTST picks`")

    market = gr.Dropdown(
        choices=["IN", "US", "UK", "SG"],
        value=DEFAULT_MARKET,
        label="Market"
    )

    chatbot = gr.ChatInterface(
        fn=lambda message, history: chat_fn(message, history, market.value),
        type="messages"
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
