from fastapi import FastAPI
import httpx
import os
import openai

app = FastAPI()

# Env Vars
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

openai.api_key = OPENAI_API_KEY

# 🔄 Récupérer prix de l'or (XAU/USD)
async def get_gold_price():
    url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVE_API_KEY}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
        return data.get("price", "Prix non disponible")

# 🤖 Générer une analyse avec GPT
async def generate_analysis(price):
    prompt = f"""Tu es un expert en trading. Le prix de l'or (XAU/USD) est actuellement à {price} USD.
Donne une analyse technique rapide et une recommandation : acheter, vendre ou attendre.
Utilise un ton professionnel et concis."""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message["content"]

# 📩 Envoi sur Telegram
async def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

# ✅ API Endpoint
@app.get("/")
async def send_market_update():
    price = await get_gold_price()
    if price == "Prix non disponible":
        return {"error": "Impossible d’obtenir le prix de l’or"}
    
    analysis = await generate_analysis(price)
    full_msg = f"📈 Prix de l’or : {price} USD\n\n🧠 Analyse IA :\n{analysis}"
    await send_to_telegram(full_msg)
    return {"status": "Envoyé", "price": price, "analysis": analysis}
