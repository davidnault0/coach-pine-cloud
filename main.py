from fastapi import FastAPI
import requests, time, os
from threading import Thread

# === CONFIGURATION ===
OANDA_API_KEY = os.getenv("OANDA_API_KEY", "colle_ta_clé_ici")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID", "101-004-xxxxxxx-001")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "bot123456789:AA...")  # Format complet
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "123456789")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-...")
ASSET = "XAU_USD"

app = FastAPI()

def get_xau_price():
    url = f"https://api-fxpractice.oanda.com/v3/accounts/{OANDA_ACCOUNT_ID}/pricing?instruments={ASSET}"
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        bids = data['prices'][0]['bids']
        price = float(bids[0]['price']) if bids else None
        return round(price, 2)
    else:
        print("Erreur OANDA:", response.status_code)
        return None

def ask_coachpine(price):
    prompt = f"""
Tu es Coach Pine, un expert du marché de l'or (XAUUSD).
Voici le prix actuel : {price}
Donne une analyse rapide :
- Tendance probable
- Action recommandée : BUY, SELL ou WAIT
- Justification courte (2–3 points max)
Réponse claire et concise.
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "gpt-4-1106-preview",
        "messages": [{"role": "user", "content": prompt}]
    }
    res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    if res.status_code == 200:
        reply = res.json()['choices'][0]['message']['content']
        return reply
    else:
        print("Erreur OpenAI:", res.text)
        return None

def send_to_telegram(msg):
    url = f"https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🧠 Coach Pine Signal:\n{msg}"
    }
    res = requests.post(url, data=data)
    if res.status_code != 200:
        print("Erreur Telegram:", res.text)

def background_loop():
    while True:
        price = get_xau_price()
        if price:
            print(f"[Coach Pine] Prix actuel : {price}")
            signal = ask_coachpine(price)
            if signal:
                send_to_telegram(signal)
        time.sleep(300)  # Toutes les 5 minutes

@app.get("/")
def root():
    return {"status": "Coach Pine actif 🚀"}

@app.on_event("startup")
def startup_event():
    Thread(target=background_loop, daemon=True).start()
