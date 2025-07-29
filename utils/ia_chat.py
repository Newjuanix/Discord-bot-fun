import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def obtener_respuesta_llama(mensaje_usuario: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "Eres un bot sarcástico y divertido que responde como si fueras un humano muy inteligente pero con un toque de humor seco, que el mensaje sea claro y en español."},
            {"role": "user", "content": mensaje_usuario}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
