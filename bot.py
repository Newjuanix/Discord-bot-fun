# bot.py

import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from keep_alive import keep_alive
from utils.curiosidades import obtener_curiosidad
from events.on_message import on_message as handle_on_message

# Cargar variables de entorno
load_dotenv()

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

# Crear instancia del bot sin comando de ayuda por defecto
bot = commands.Bot(command_prefix='?', intents=intents, help_command=None)

# Variable para rastrear si los comandos ya fueron sincronizados
comandos_sincronizados = False

# Función para cargar comandos desde carpeta 'commands'
async def cargar_extensiones():
    global comandos_sincronizados
    try:
        # Cargar cada archivo de comandos
        for filename in os.listdir('./commands'):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = f'commands.{filename[:-3]}'
                try:
                    await bot.load_extension(module_name)
                    print(f"✅ {module_name} cargado correctamente.")
                except Exception as e:
                    print(f'❌ Error al cargar {module_name}: {e}')
        
        # Sincronizar comandos de barra si no se han sincronizado
        if not comandos_sincronizados:
            await bot.tree.sync()
            print("✅ Comandos de barra sincronizados.")
            comandos_sincronizados = True
            
    except Exception as e:
        print(f'❌ Error al cargar extensiones: {e}')

# Mantener vivo (Replit, etc.)
keep_alive()

@bot.event
async def setup_hook():
    # Cargar extensiones cuando el bot se está iniciando
    await cargar_extensiones()
    print('✅ Extensiones cargadas')

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} se ha conectado a Discord.')
    enviar_curiosidad.start()

@bot.event
async def on_message(message):
    # Filtrar mensajes del propio bot
    if message.author.bot:
        return
        
    # Primero procesar comandos
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return  # Salir después de procesar comandos
        
    # Luego manejar otros mensajes con la función personalizada
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
            embed.set_footer(text="Más curiosidades cada hora 👀")
            await canal.send(embed=embed)
    else:
        print("⚠️ No se encontró el canal para curiosidades.")

# Iniciar el bot
bot.run(os.getenv("DISCORD_TOKEN"))
