import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def obtener_respuesta_llama(mensajes: list) -> str:
    """
    Obtiene una respuesta de la IA basada en el historial de la conversación.
    
    Args:
        mensajes: Lista de diccionarios con el formato [{"role": "user/assistant/system", "content": "texto"}, ...]
                Debe incluir al menos un mensaje de sistema y uno de usuario.
    """
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ Error: No se encontró la clave API de OpenRouter")
            return "Lo siento, estoy teniendo problemas técnicos. Por favor, inténtalo más tarde."

        # Verificar que haya al menos un mensaje de sistema
        has_system = any(msg.get("role") == "system" for msg in mensajes)
        if not has_system:
            # Si no hay mensaje de sistema, agregar uno por defecto
            system_msg = {"role": "system", "content": "Eres un asistente de soporte amable y servicial. Mantén tus respuestas concisas pero útiles. Si no entiendes algo, pide más detalles."}
            mensajes.insert(0, system_msg)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-github/repo-name"  # Reemplaza con tu repo
        }

        body = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": mensajes,
            "temperature": 0.7,  # Controla la creatividad de las respuestas
            "max_tokens": 500,   # Límite de longitud de respuesta
            "stop": ["\n"]      # Detenerse en saltos de línea para respuestas más concisas
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body) as resp:
                data = await resp.json()
                
                # Verificar si hay un error en la respuesta
                if 'error' in data:
                    print(f"❌ Error de la API: {data.get('error', {}).get('message', 'Error desconocido')}")
                    return "Vaya, parece que estoy teniendo un problema para pensar. ¿Podrías intentarlo de nuevo?"
                    
                # Verificar la estructura de la respuesta
                if 'choices' in data and len(data['choices']) > 0:
                    return data["choices"][0].get("message", {}).get("content", "No pude generar una respuesta en este momento.")
                else:
                    print(f"❌ Respuesta inesperada de la API: {data}")
                    return "Mi cerebro está un poco confundido ahora mismo. ¿Podrías reformular tu pregunta?"
                    
    except aiohttp.ClientError as e:
        print(f"❌ Error de conexión: {str(e)}")
        return "Parece que estoy teniendo problemas para conectarme. ¿Podrías intentarlo más tarde?"
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return "¡Ups! Algo salió mal. Por favor, inténtalo de nuevo en un momento."
