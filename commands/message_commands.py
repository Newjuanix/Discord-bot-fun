import discord
from discord import app_commands
from discord.ext import commands

class MessageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ROL_PERMITIDO_ID = 1391931720730808382  # Mismo ID de rol que en otros comandos

    def tiene_permiso(self, miembro):
        return miembro and any(rol.id == self.ROL_PERMITIDO_ID for rol in miembro.roles)

    @app_commands.command(
        name="msg",
        description="Envía un mensaje a un canal o usuario"
    )
    @app_commands.describe(
        mensaje="El mensaje a enviar",
        usuario="Usuario al que enviar el mensaje (dejar vacío para enviar al canal actual)"
    )
    async def enviar_mensaje(
        self,
        interaction: discord.Interaction,
        mensaje: str,
        usuario: discord.Member = None
    ):
        # Verificar permisos
        if not self.tiene_permiso(interaction.user):
            await interaction.response.send_message(
                "🚫 No tienes permiso para usar este comando.",
                ephemeral=True
            )
            return

        try:
            if usuario is None:
                # Enviar al canal actual
                await interaction.channel.send(mensaje)
                await interaction.response.send_message(
                    "✅ Mensaje enviado al canal.",
                    ephemeral=True
                )
            else:
                # Enviar mensaje directo al usuario
                try:
                    await usuario.send(mensaje)
                    await interaction.response.send_message(
                        f"✅ Mensaje enviado a {usuario.mention}.",
                        ephemeral=True
                    )
                except discord.Forbidden:
                    await interaction.response.send_message(
                        f"❌ No se pudo enviar el mensaje a {usuario.mention}. "
                        "El usuario tiene los mensajes directos desactivados.",
                        ephemeral=True
                    )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Ocurrió un error: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(MessageCommands(bot))