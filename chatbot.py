from openai import OpenAI
import re
import os

# 🔐 Your actual API key here
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🧠 Conversation memory
messages = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant for lead generation. Ask the user their name, email, and what service they are interested in. Keep the conversation natural and friendly."
    }
]

# 📝 Lead data
lead_data = {
    "name": None,
    "email": None,
    "interest": None
}

# 🧠 Extract info from user input
def extract_lead_info(user_input):
    # Email extraction
    if not lead_data['email']:
        email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', user_input)
        if email_match:
            lead_data['email'] = email_match.group()
            print("[✅] Email captured:", lead_data['email'])

    # Name extraction
    if not lead_data['name']:
        if "my name is" in user_input.lower():
            lead_data['name'] = user_input.split("is")[-1].strip().split()[0]
            print("[✅] Name captured:", lead_data['name'])

    # Interest extraction
    if not lead_data['interest']:
        if "interested in" in user_input.lower():
            lead_data['interest'] = user_input.split("interested in")[-1].strip()
            print("[✅] Interest captured:", lead_data['interest'])

# 📝 Save lead to file
def save_lead():
    with open("leads.txt", "a") as file:
        file.write(f"{lead_data['name']} | {lead_data['email']} | {lead_data['interest']}\n")
    print("🔐 Lead saved!")
    print("[📂] Saved to:", os.path.abspath("leads.txt"))

# 💬 Respond to user
def chatbot_response(user_input):
    messages.append({"role": "user", "content": user_input})
    extract_lead_info(user_input)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    if all(lead_data.values()):
        print("✅ Collected all lead info:", lead_data)
        save_lead()

    return reply

# 🔁 Chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Bot: Goodbye, co-founder!")
        break
    reply = chatbot_response(user_input)
    print("Bot:", reply)


