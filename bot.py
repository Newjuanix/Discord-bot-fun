# bot.py

import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from keep_alive import keep_alive
from utils.curiosidades import obtener_curiosidad
from events.on_message import on_message as handle_on_message
from events.on_message import tickets_con_staff  # para no responder si ya llamaron staff
from utils.verification import iniciar_verificacion, manejar_respuesta_verificacion
from utils.ia_chat import obtener_respuesta_llama
from config import (
    CATEGORIA_TICKETS,
    CANAL_VERIFICACION,
    ROL_VERIFICADO
)
import time

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

# Estados compartidos de verificación:
estados_verificacion = {}

# Cooldown por usuario (para menciones)
cooldown_menciones = {}  # {user_id: timestamp_ultimo_mensaje}

# Bot
bot = commands.Bot(command_prefix='?', intents=intents, help_command=None)

# Estado por canal de ticket
canales_ticket = {}

# Mantener vivo
keep_alive()

# Carga de extensiones
async def cargar_extensiones():
    try:
        for filename in os.listdir('./commands'):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = f'commands.{filename[:-3]}'
                try:
                    await bot.load_extension(module_name)
                    print(f"✅ {module_name} cargado correctamente.")
                except Exception as e:
                    print(f'❌ Error al cargar {module_name}: {e}')
        await bot.tree.sync()
        print("✅ Comandos de barra sincronizados.")
    except Exception as e:
        print(f'❌ Error al cargar extensiones: {e}')

@bot.event
async def setup_hook():
    await cargar_extensiones()
    print('✅ Extensiones cargadas')

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} se ha conectado a Discord.')
    enviar_curiosidad.start()
    activity = discord.Activity(
        type=discord.ActivityType.watching,  # watching = "Viendo ..."
        name="Mi creador: juanix.is-a.dev"       # texto que aparece
    )
    await bot.change_presence(activity=activity)

@bot.event
async def on_message(message: discord.Message):
    # Ignorar mensajes del propio bot
    if message.author.bot:
        return

    # Si en este canal ya se llamó al staff, no responder nada más
    if message.channel.id in tickets_con_staff:
        return

    # Comandos con prefijo
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # ----------------------------
    #   BLOQUE: SOLO TICKETS
    # ----------------------------
    is_ticket = hasattr(message.channel, 'category') and message.channel.category_id == CATEGORIA_TICKETS
    mensaje_lower = message.content.lower().strip()

    if is_ticket:
        # Mantener estado del canal
        if message.channel.id not in canales_ticket:
            canales_ticket[message.channel.id] = {"historial_chat": [], "instrucciones_enviadas": False}

        # Instrucciones una sola vez
        if not canales_ticket[message.channel.id]["instrucciones_enviadas"]:
            msg_instr = (
                "¡Hola! Soy el asistente de soporte.\n\n"
                "🔹 Si te quieres verificar, escribe: **verificar**\n"
                "🔹 Si necesitas ayuda con algo más, cuéntame y con gusto te ayudaré.\n"
                "🔹 Para notificar al staff y cerrar el chat, escribe: **llamar staff**"
            )
            await message.channel.send(msg_instr)
            canales_ticket[message.channel.id]["instrucciones_enviadas"] = True

        # Parar chat
        if mensaje_lower == 'parar chat':
            historial = canales_ticket.get(message.channel.id, {}).get("historial_chat", [])
            if historial:
                texto_historial = "\n".join(
                    [("Usuario: " if m.get("role") == "user" else "Bot: ") + m.get("content", "")
                     for m in historial if m.get("content", "").lower() != "parar chat"]
                )
                resumen = await obtener_respuesta_llama(
                    "Genera un resumen conciso de esta conversación para el staff:\n\n" + texto_historial
                )
                embed = discord.Embed(
                    title="📝 Resumen de conversación",
                    description=resumen,
                    color=discord.Color.blue()
                )
                embed.add_field(name="Canal", value=message.channel.mention, inline=True)
                embed.add_field(name="Usuario", value=message.author.mention, inline=True)

                canal_verificacion = bot.get_channel(CANAL_VERIFICACION)
                if canal_verificacion:
                    await canal_verificacion.send("📢 **Se ha solicitado asistencia de staff**", embed=embed)

                await message.channel.send("✅ He notificado al staff. Por favor, espera a que te atiendan.")
                canales_ticket[message.channel.id]["historial_chat"] = []
                return
            else:
                await message.channel.send("No hay historial de conversación para enviar al staff.")
                return

        # Verificación
        if mensaje_lower in ('verificar', 'me quiero verificar'):
            try:
                await iniciar_verificacion(bot, message, estados_verificacion)
            except Exception as e:
                print(f"ERROR en iniciar_verificacion: {e}")
                await message.channel.send("❌ Ocurrió un error al iniciar la verificación. Por favor, inténtalo de nuevo.")
            return

        # Continuar verificación
        user_id = message.author.id
        if user_id in estados_verificacion:
            estado = estados_verificacion[user_id]
            canal_esperado = estado.get("canal_ticket_id")
            if canal_esperado == message.channel.id:
                try:
                    manejado = await manejar_respuesta_verificacion(bot, message, estados_verificacion)
                    if manejado or (user_id not in estados_verificacion):
                        return
                except Exception as e:
                    print(f"ERROR en manejar_respuesta_verificacion: {e}")
                    return
            else:
                await message.channel.send("⚠️ Continúa tu verificación en el canal de tu ticket.")
                return

        # Delegar soporte
        handled = await handle_on_message(bot, message)
        if handled:
            return

        # Fallback IA en tickets
        canales_ticket[message.channel.id]["historial_chat"].append({"role": "user", "content": message.content})
        if len(canales_ticket[message.channel.id]["historial_chat"]) > 20:
            canales_ticket[message.channel.id]["historial_chat"] = canales_ticket[message.channel.id]["historial_chat"][-20:]

        contexto = [
            {"role": "system",
             "content": "Eres un asistente de soporte amable y servicial. Mantén tus respuestas concisas pero útiles. Si no entiendes algo, pide más detalles."}
        ]
        contexto.extend(canales_ticket[message.channel.id]["historial_chat"])

        respuesta = await obtener_respuesta_llama(contexto)
        canales_ticket[message.channel.id]["historial_chat"].append({"role": "assistant", "content": respuesta})
        await message.channel.send(respuesta)
        return

    # ----------------------------
    #   Fuera de tickets
    # ----------------------------
    ahora = time.time()
    user_id = message.author.id

    # Menciones fuera de tickets con cooldown 3s
    if bot.user in message.mentions:
        if user_id in cooldown_menciones and ahora - cooldown_menciones[user_id] < 3:
            return
        cooldown_menciones[user_id] = ahora
        await handle_on_message(bot, message)
        return

    # Default
    await handle_on_message(bot, message)


@tasks.loop(hours=5)
async def enviar_curiosidad():
    canal_id = os.getenv("CURIOSIDADES_CHANNEL_ID")
    if not canal_id:
        print("⚠️ Falta la variable de entorno CURIOSIDADES_CHANNEL_ID.")
        return

    canal = bot.get_channel(int(canal_id))
    if canal:
        curiosidad = await obtener_curiosidad()
        if curiosidad:
            embed = discord.Embed(
                title="📢 Curiosidad del momento",
                description=curiosidad.strip(),
                color=discord.Color.orange()
            )
            embed.set_footer(text="Más curiosidades cada 5 horas 👀")
            await canal.send(embed=embed)
    else:
        print("⚠️ No se encontró el canal para curiosidades.")

bot.run(os.getenv("DISCORD_TOKEN"))
