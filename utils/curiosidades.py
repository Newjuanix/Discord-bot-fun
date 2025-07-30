from utils.ia_chat import obtener_respuesta_llama

async def obtener_curiosidad(bot=None):
    prompt = [
        {"role": "system", "content": "Eres un asistente que proporciona datos curiosos interesantes. Responde solo con el dato curioso, sin introducciones ni despedidas."},
        {"role": "user", "content": "Dame un dato curioso corto y divertido. Solo el dato, sin introducciones ni despedidas."}
    ]
    try:
        curiosidad = await obtener_respuesta_llama(prompt)
        return curiosidad
    except Exception as e:
        print(f"Error al obtener curiosidad: {e}")
        return "¡Ups! Algo salió mal al obtener una curiosidad. ¿Quieres que lo intente de nuevo?"
