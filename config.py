# config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener configuración
try:
    CANAL_PERMITIDO = int(os.getenv('CANAL_PERMITIDO'))
except (ValueError, TypeError):
    CANAL_PERMITIDO = None
    print("⚠️ No se configuró CANAL_PERMITIDO o el valor no es válido. El bot funcionará en todos los canales.")

# Configuración de verificación
CANAL_VERIFICACION = 1321309769616719985  # ID del canal donde se enviarán las verificaciones
ROL_VERIFICADO = 1385472897300168815      # ID del rol a asignar cuando se verifique
ROL_NO_VERIFICADO = 1384674781751677080   # ID del rol a quitar cuando se verifique (reemplaza con el ID correcto)
CATEGORIA_TICKETS = 1321290268938469426   # ID de la categoría donde se crean los tickets

# Otras configuraciones globales
PREFIX = "?"
ROL_PERMITIDO_ID = 1321304860548792330  # ID del rol con permisos
ROL_STAFF = 1321555751805653012  # ID del rol de staff (usar el mismo que ROL_PERMITIDO_ID por defecto)

PALABRAS_PROHIBIDAS = [
    "código", "codigo", "script", "archivo",
    "secreto", "source", "fuente", "contraseña",
    "api key", "token"
]

# Estados de verificación
class EstadosVerificacion:
    ESPERANDO_INVITADOR = 1
    ESPERANDO_NICK_ROBLOX = 2
    ESPERANDO_GRUPO_BLOX = 3
    ENVIANDO_VERIFICACION = 4
