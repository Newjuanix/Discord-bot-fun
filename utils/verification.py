# utils/verification.py

import discord
from discord import ui
from config import CANAL_VERIFICACION, ROL_VERIFICADO, CATEGORIA_TICKETS, ROL_NO_VERIFICADO

# Pasos de verificación
PASOS_VERIFICACION = [
    {"pregunta": "¿Quién te invitó a nuestro servidor? (Menciona al usuario con @ o escribe su nombre)", "campo": "invitador"},
    {"pregunta": "¿Cuál es tu nombre de usuario de Roblox?", "campo": "usuario_roblox"},
    {"pregunta": "¿Perteneces a algún otro grupo de Blox? (Responde con 'sí' o 'no' y especifica cuál si es el caso)", "campo": "otro_grupo"},
]


class VerificacionView(ui.View):
    def __init__(self, user_id, datos_verificacion):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.datos = datos_verificacion  # {"canal_ticket_id": int, "datos": {...}}

    @ui.button(label="✅ Aceptar", style=discord.ButtonStyle.green, custom_id="verificar_aceptar")
    async def aceptar(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("No tienes permisos para realizar esta acción.", ephemeral=True)
            return

        await interaction.response.defer()
        try:
            guild = interaction.guild
            miembro = await guild.fetch_member(self.user_id)
            if not miembro:
                await interaction.followup.send("❌ No se pudo encontrar al miembro en el servidor.", ephemeral=True)
                return

            rol_verificado = guild.get_role(ROL_VERIFICADO)
            rol_no_verificado = guild.get_role(ROL_NO_VERIFICADO)

            if rol_verificado and rol_verificado not in miembro.roles:
                await miembro.add_roles(rol_verificado, reason="Verificación aprobada por un moderador")
                if rol_no_verificado and rol_no_verificado in miembro.roles:
                    await miembro.remove_roles(rol_no_verificado, reason="Usuario verificado exitosamente")

                # Actualizar embed
                embed = interaction.message.embeds[0]
                embed.color = discord.Color.green()
                embed.set_footer(text=f"Aceptado por: {interaction.user.display_name}")
                await interaction.message.edit(embed=embed, view=None)

                # Avisar en el ticket
                canal_ticket_id = None
                if isinstance(self.datos, dict):
                    canal_ticket_id = self.datos.get('canal_ticket_id')
                else:
                    canal_ticket_id = int(self.datos) if str(self.datos).isdigit() else None
                if canal_ticket_id:
                    canal_ticket = guild.get_channel(int(canal_ticket_id))
                    if canal_ticket:
                        await canal_ticket.send(f"¡Felicidades {miembro.mention}! Has sido verificado correctamente. 🎉")

                await interaction.followup.send("✅ Usuario verificado exitosamente.", ephemeral=True)
            else:
                await interaction.followup.send("⚠️ El usuario ya está verificado o el rol no existe.", ephemeral=True)
        except Exception as e:
            print(f"Error en aceptar verificación: {e}")
            await interaction.followup.send("❌ Ocurrió un error al procesar la verificación.", ephemeral=True)

    @ui.button(label="❌ Rechazar", style=discord.ButtonStyle.red, custom_id="verificar_rechazar")
    async def rechazar(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("No tienes permisos para realizar esta acción.", ephemeral=True)
            return

        # Modal para explicar la razón del rechazo
        class RazonRechazoModal(ui.Modal, title="Razón del Rechazo"):
            razon = ui.TextInput(label="Motivo del rechazo", style=discord.TextStyle.paragraph, required=True, max_length=500)
            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer()
                self.stop()

        modal = RazonRechazoModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.razon.value:
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            embed.set_footer(text=f"Rechazado por: {interaction.user.display_name}")
            await interaction.message.edit(embed=embed, view=None)

            try:
                canal_ticket_id = self.datos.get('canal_ticket_id') if isinstance(self.datos, dict) else None
                if canal_ticket_id:
                    canal_ticket = interaction.guild.get_channel(canal_ticket_id)
                    if canal_ticket:
                        await canal_ticket.send(
                            f"❌ Tu solicitud de verificación ha sido rechazada.\n**Razón:** {modal.razon.value}"
                        )
            except Exception:
                pass


# -------------------- API del módulo --------------------

async def iniciar_verificacion(bot, message: discord.Message, estados_verificacion: dict):
    """
    Inicia el proceso de verificación para un usuario (solo en tickets).
    Si el usuario ya tiene el rol de verificado, responde que ya está verificado.
    """
    user_id = message.author.id
    print(f"\n=== DEBUG: Iniciando verificación para {message.author.name} (ID: {user_id}) ===")

    # 1) Si ya tiene el rol de verificado -> avisar y salir
    try:
        guild = message.guild
        miembro = guild.get_member(user_id) or await guild.fetch_member(user_id)
        rol_verificado = guild.get_role(ROL_VERIFICADO)
        if rol_verificado and miembro and (rol_verificado in miembro.roles):
            estados_verificacion.pop(user_id, None)  # por si había quedado algo pendiente
            await message.channel.send(f"✅ {miembro.mention}, **ya estás verificado**. No necesitas hacer el proceso.")
            return
    except Exception as e:
        print(f"DEBUG: No se pudo verificar rol de verificado al iniciar: {e}")

    # 2) Evitar doble inicio
    if user_id in estados_verificacion:
        paso_actual = estados_verificacion[user_id].get("paso_actual", 0)
        if paso_actual < len(PASOS_VERIFICACION):
            pregunta_actual = PASOS_VERIFICACION[paso_actual]["pregunta"]
            await message.channel.send(
                f"Ya estás en proceso de verificación. Por favor, responde a la pregunta actual:\n\n**{pregunta_actual}**"
            )
        else:
            await message.channel.send(
                "Ya has completado el proceso de verificación. Espera a que un administrador revise tu solicitud."
            )
        return

    # 3) Crear estado
    estados_verificacion[user_id] = {
        "canal_ticket_id": message.channel.id,
        "paso_actual": 0,
        "datos": {}
    }

    # 4) Enviar primera pregunta
    embed = discord.Embed(
        title="🔍 Proceso de Verificación",
        description="¡Hola! Vamos a comenzar con tu verificación. Por favor, responde a las siguientes preguntas:\n\n"
                    f"**1/{len(PASOS_VERIFICACION)}** {PASOS_VERIFICACION[0]['pregunta']}",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Responde con 'cancelar' en cualquier momento para cancelar la verificación.")
    await message.channel.send(embed=embed)


async def manejar_respuesta_verificacion(bot, message: discord.Message, estados_verificacion: dict) -> bool:
    """
    Procesa cada respuesta del usuario durante la verificación.
    Devuelve:
      True  -> el mensaje fue parte del flujo (la IA NO debe responder)
      False -> el flujo terminó o no aplica
    """
    user_id = message.author.id
    print(f"\n=== DEBUG: Iniciando manejo de respuesta para usuario {user_id} ===")
    print(f"DEBUG: Estado actual de verificación: {estados_verificacion.get(user_id, 'No encontrado')}")

    # A) Si ya tiene el rol de verificado (por ejemplo, se lo dieron antes o a mitad del proceso)
    try:
        guild = message.guild
        miembro = guild.get_member(user_id) or await guild.fetch_member(user_id)
        rol_verificado = guild.get_role(ROL_VERIFICADO)
        if rol_verificado and miembro and (rol_verificado in miembro.roles):
            estados_verificacion.pop(user_id, None)
            await message.channel.send("✅ **Ya cuentas con el rol de verificado.** No necesitas continuar el proceso.")
            return True  # ya respondimos
    except Exception as e:
        print(f"DEBUG: No se pudo verificar rol de verificado durante el flujo: {e}")

    # B) ¿Está en verificación?
    estado = estados_verificacion.get(user_id)
    if not estado:
        return False

    # C) ¿En el canal correcto?
    canal_esperado = estado.get("canal_ticket_id")
    if not canal_esperado or message.channel.id != canal_esperado:
        print(f"DEBUG: Canal incorrecto. Actual: {message.channel.id}, Esperado: {canal_esperado}")
        await message.channel.send("⚠️ Continúa tu verificación en el canal de tu ticket.")
        return True  # evitamos que responda la IA

    # D) Cancelar
    if message.content.lower().strip() == 'cancelar':
        estados_verificacion.pop(user_id, None)
        await message.channel.send("❌ Has cancelado el proceso de verificación.")
        return True

    # E) Paso actual válido
    paso_actual = estado.get("paso_actual", 0)
    if paso_actual < 0 or paso_actual >= len(PASOS_VERIFICACION):
        await message.channel.send("❌ Error en el proceso de verificación. Inícialo nuevamente con **verificar**.")
        estados_verificacion.pop(user_id, None)
        return True

    # F) Guardar respuesta
    campo = PASOS_VERIFICACION[paso_actual].get("campo", f"pregunta_{paso_actual}")
    estado.setdefault("datos", {})[campo] = message.content

    # G) ¿Hay más preguntas?
    if paso_actual + 1 < len(PASOS_VERIFICACION):
        estado["paso_actual"] = paso_actual + 1
        siguiente = PASOS_VERIFICACION[estado["paso_actual"]]
        embed = discord.Embed(
            title=f"Pregunta {estado['paso_actual'] + 1} de {len(PASOS_VERIFICACION)}",
            description=siguiente['pregunta'],
            color=discord.Color.blue()
        )
        if 'opciones' in siguiente and siguiente['opciones']:
            opciones_texto = "\n".join([f"• {op}" for op in siguiente['opciones']])
            embed.add_field(name="Opciones:", value=opciones_texto, inline=False)
        await message.channel.send(embed=embed)
        return True

    # H) Fin -> enviar solicitud a revisión y limpiar
    await finalizar_verificacion(bot, user_id, estados_verificacion)
    return True


async def finalizar_verificacion(bot, user_id: int, estados_verificacion: dict):
    """
    Finaliza: arma embed, lo envía a CANAL_VERIFICACION y limpia estado.
    """
    estado = estados_verificacion.get(user_id)
    if not estado:
        return

    datos = estado.get("datos", {})
    canal_id = estado.get("canal_ticket_id")
    canal_ticket = bot.get_channel(canal_id) if canal_id else None

    embed = discord.Embed(
        title="📝 Solicitud de Verificación",
        description=f"Usuario: <@{user_id}>\n"
                    f"Canal: {canal_ticket.mention if canal_ticket else 'Desconocido'}",
        color=discord.Color.gold()
    )
    for i, paso in enumerate(PASOS_VERIFICACION):
        campo = paso["campo"]
        valor = datos.get(campo, "No proporcionado")
        embed.add_field(name=f"{i+1}. {paso['pregunta']}", value=valor, inline=False)

    canal_verificacion = bot.get_channel(CANAL_VERIFICACION)
    if canal_verificacion:
        view = VerificacionView(user_id, {"canal_ticket_id": canal_id, "datos": datos})
        await canal_verificacion.send(embed=embed, view=view)
        if canal_ticket:
            await canal_ticket.send("✅ ¡Gracias por completar la verificación! Tu solicitud ha sido enviada al equipo de staff para su revisión.")

    # Limpiar estado
    estados_verificacion.pop(user_id, None)
