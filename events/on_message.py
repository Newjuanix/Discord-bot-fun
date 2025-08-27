# events/on_message.py

import random
import discord
import time
from utils.ia_chat import obtener_respuesta_llama
from utils.shared_data import usuarios_chat
from config import (
    CANAL_PERMITIDO,
    PREFIX,
    ROL_PERMITIDO_ID,
    PALABRAS_PROHIBIDAS,
    CATEGORIA_TICKETS,
    ROL_STAFF
)

# Tickets donde el staff fue llamado (desactivar auto-chat)
tickets_con_staff = set()

# Cooldown por usuario para menciones
cooldown_menciones = {}  # {user_id: timestamp_ultimo_mensaje}

async def handle_staff_call(message: discord.Message):
    tickets_con_staff.add(message.channel.id)
    print(f"DEBUG: Canal {message.channel.id} marcado para no responder más")

    staff_mentioned = False
    async for msg in message.channel.history(limit=10):
        if msg.author == message.guild.me and "🔔 **¡Se ha notificado al staff!**" in msg.content:
            staff_mentioned = True
            break

    try:
        guild = message.guild
        staff_role = guild.get_role(ROL_STAFF)
        if staff_role and not staff_mentioned:
            await message.channel.send(
                f"🔔 **¡Se ha notificado al staff!** {staff_role.mention}\n"
                f"Usuario: {message.author.mention} ha solicitado asistencia en {message.channel.mention}.\n"
                "El chat automático se ha desactivado. Un miembro del staff atenderá tu solicitud pronto."
            )
        else:
            await message.channel.send(
                "🔔 **¡Se ha notificado al staff!**\n"
                f"Usuario: {message.author.mention} ha solicitado asistencia en {message.channel.mention}.\n"
                "El chat automático se ha desactivado. Un miembro del staff atenderá tu solicitud pronto."
            )
            if not staff_role:
                print(f"⚠️ No se encontró el rol de staff con ID: {ROL_STAFF}")
    except Exception as e:
        print(f"ERROR al notificar al staff: {e}")
        try:
            await message.channel.send(
                "🔔 **¡Se ha notificado al staff!**\n"
                "El chat automático se ha desactivado. Un miembro del staff atenderá tu solicitud pronto."
            )
        except Exception as e2:
            print(f"ERROR crítico al notificar: {e2}")

    return True


# Cooldown global de 4 segundos entre respuestas
last_message_time = 0

async def on_message(bot, message: discord.Message):
    global last_message_time

    # Ignorar bots salvo mención explícita
    if message.author.bot and bot.user not in message.mentions:
        return False

    # Cooldown general 4s
    now = time.time()
    if now - last_message_time < 4:
        return False
    last_message_time = now

    # No responder si el canal ya llamó staff
    if message.channel.id in tickets_con_staff:
        return True

    contenido = message.content.lower().strip()
    canal_id = message.channel.id
    autor_id = message.author.id

    # Detectar tickets
    is_ticket_channel = hasattr(message.channel, 'category') and message.channel.category_id == CATEGORIA_TICKETS

    # Manejar 'llamar staff' solo en tickets
    if is_ticket_channel and contenido == "llamar staff":
        return await handle_staff_call(message)

    # Respuesta aleatoria 5% en cualquier canal
    if random.random() < 0.05:
        try:
            prompt = f"Responde con sarcasmo y estilo humano este mensaje: \"{message.content}\". Que sea corto, divertido, nada de mensajes de ayuda, claro y en español."
            respuesta = await obtener_respuesta_llama([{"role": "user", "content": prompt}])
            await message.channel.send(respuesta)
            return True
        except Exception as e:
            print(f"Error en respuesta aleatoria: {e}")

    # Comandos con prefijo los maneja bot.py
    if contenido.startswith(PREFIX):
        return False

    # Mención directa al bot en cualquier canal
    if bot.user in message.mentions:
        if any(p in contenido for p in PALABRAS_PROHIBIDAS):
            await message.channel.send("❌ Lo siento, no puedo compartir información confidencial.")
        else:
            prompt = [
                {"role": "system",
                 "content": f"Responde con sarcasmo y estilo humano este mensaje: \"{message.content}\". Que sea corto, divertido, claro y en español."},
                {"role": "user", "content": message.content}
            ]
            respuesta = await obtener_respuesta_llama(prompt)
            await message.channel.send(respuesta)
        return True

    # Soporte dentro de tickets
    if is_ticket_channel and not contenido.startswith(PREFIX):
        if canal_id in tickets_con_staff:
            return False
        async with message.channel.typing():
            try:
                prompt = [
                    {"role": "system",
                     "content": "Eres un asistente de soporte profesional y atento. Responde de manera clara, concisa y útil. Mantén un tono amable y profesional. Si el usuario necesita ayuda con la verificación, guíalo amablemente, pero como ser humano."},
                    {"role": "user", "content": message.content}
                ]
                respuesta = await obtener_respuesta_llama(prompt)
                await message.reply(respuesta, mention_author=True)
                return True
            except Exception as e:
                print(f"Error al generar respuesta de IA: {e}")
                return False

    # Conversaciones activas fuera de tickets
    if canal_id in usuarios_chat and autor_id in usuarios_chat[canal_id]:
        if not contenido.startswith(PREFIX):
            async with message.channel.typing():
                prompt = [
                    {"role": "system",
                     "content": f"Responde con sarcasmo y estilo humano este mensaje: \"{message.content}\". Que sea corto, divertido, claro y en español."},
                    {"role": "user", "content": message.content}
                ]
                respuesta = await obtener_respuesta_llama(prompt)
                await message.channel.send(respuesta)
            return True

    return False
