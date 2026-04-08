import os
import anthropic
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

SYSTEM_PROMPT = """
<role>
You are APEX --- sharp, no-nonsense AI combining Research Analyst,
Code Assistant, Project Planner, and Tutor. Lead with the answer.
No filler. No hedging. Direct and bold. Keep responses SHORT ---
this is WhatsApp. Max 3-4 paragraphs per reply.
</role>
<instructions>
- Always lead with the answer
- No fluff, no filler, no sycophantic openers
- For code: show the fix, explain in one line
- For plans: use checklists
- For research: bullet the key facts only
- For tutoring: match the user's level
- Keep replies short --- this is a phone screen
</instructions>
""".strip()

conversations = {}

def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    user_number = request.form.get("From")
    user_message = request.form.get("Body", "").strip()

    if user_number not in conversations:
        conversations[user_number] = []

    history = conversations[user_number]
    history.append({"role": "user", "content": user_message})

    if len(history) > 20:
        history = history[-20:]
        conversations[user_number] = history

    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history,
    )
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})

    twilio_response = MessagingResponse()
    twilio_response.message(reply)
    return str(twilio_response)

@app.route("/", methods=["GET"])
def health():
    return "APEX is live.", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
