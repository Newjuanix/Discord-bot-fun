from utils.ia_chat import obtener_respuesta_llama

async def obtener_curiosidad(bot=None):
    prompt = "Dame solo un dato curioso corto y divertido. No digas 'Aquí tienes' ni nada adicional. Solo el dato."
    curiosidad = await obtener_respuesta_llama(prompt)
    return curiosidad
