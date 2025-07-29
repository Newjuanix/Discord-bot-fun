# events/on_message.py

import random
import discord
from utils.ia_chat import obtener_respuesta_llama
from utils.shared_data import usuarios_chat

PREFIX = "?"
ROL_PERMITIDO_ID = 1391931720730808382  # Mismo ID que en chat_commands.py

PALABRAS_PROHIBIDAS = [
    "código", "codigo", "script", "archivo",
    "secreto", "source", "fuente", "contraseña",
    "api key", "token"
]

async def on_message(bot, message: discord.Message):
    if message.author.bot:
        return

    contenido = message.content.lower()
    canal_id = message.channel.id
    autor_id = message.author.id

    miembro = message.guild.get_member(autor_id)
    tiene_permiso = miembro and any(rol.id == ROL_PERMITIDO_ID for rol in miembro.roles)

    # Los comandos ya se manejan en bot.py
    if contenido.startswith(PREFIX):
        return

    # 🤖 Si mencionan al bot directamente
    if bot.user in message.mentions:
        if any(p in contenido for p in PALABRAS_PROHIBIDAS):
            await message.channel.send("❌ Lo siento, no puedo compartir información confidencial.")
        else:
            respuesta = await obtener_respuesta_llama(message.content)
            await message.channel.send(respuesta)
        return

    # 💬 Conversaciones activas
    if canal_id in usuarios_chat and autor_id in usuarios_chat[canal_id]:
        # No responder si el mensaje es un comando
        if not message.content.startswith(PREFIX):
            async with message.channel.typing():
                respuesta = await obtener_respuesta_llama(message.content)
                await message.reply(respuesta, mention_author=True)
        return

    # 🎲 Respuesta aleatoria con 5% de probabilidad
    if random.random() < 0.05:
        prompt = f"Responde con sarcasmo y estilo humano este mensaje: \"{message.content}\". Que sea corto, divertido, claro y en español."
        respuesta = await obtener_respuesta_llama(prompt)
        await message.channel.send(respuesta)
