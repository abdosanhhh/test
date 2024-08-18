from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import requests, os

# Load environment variables from .env file
load_dotenv("v.env")

# Retrieve environment variables
URL = os.getenv("URL")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
FB_API_KEY = os.getenv("FB_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
V_TOKEN = os.getenv("V_TOKEN")

# Set up headers for API requests
HEADERS = {
    "Authorization": f"Bearer {FB_API_KEY}",
    "Content-Type": "application/json"
}

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

# Function to generate AI responses using the Groq API
def ai(prompt: str) -> str:
    try:
        message = []
        completion = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=8192,
            top_p=1,
            stream=True,
            stop=None,
        )
        for chunk in completion:
            response = chunk.choices[0].delta.content or ""
            message.append(response)
        full_response = "".join(message)
        return full_response
    except Exception as e:
        return "Sorry, I encountered an issue processing your request."

# Function to send a response back to the user via WhatsApp
def send(response: str) -> None:
    try:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": PHONE_NUMBER,
            "type": "text",
            "text": {"body": response}
        }
        response = requests.post(URL, headers=HEADERS, json=data)
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

# Initialize the Flask app
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello World", 200

@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == V_TOKEN:
            return request.args.get('hub.challenge'), 200
        else:
            return 'Verification Error!', 403

    if request.method == 'POST':
        try:
            data = request.json
            messages = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            response = ai(messages)
            send(response)
        except Exception as e:
            pass
        finally:
            return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(debug=True)