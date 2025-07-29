from discord.ext import commands
from utils.shared_data import usuarios_chat

class ChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ROL_PERMITIDO_ID = 1391931720730808382  # ID del rol con permisos

    def tiene_permiso(self, miembro):
        return miembro and any(rol.id == self.ROL_PERMITIDO_ID for rol in miembro.roles)

    @commands.command(name="startchat")
    async def startchat(self, ctx):
        miembro = ctx.author
        if not self.tiene_permiso(miembro):
            await ctx.send("🚫 No tienes permisos para iniciar una conversación.")
            return

        canal_id = ctx.channel.id
        usuarios_chat[canal_id] = {miembro.id}
        await ctx.send("✅ Conversación con IA iniciada. Ahora puedes hablar conmigo sin necesidad de mencionarme. Usa `?adduser @usuario` para agregar a alguien más o `?endchat` para terminar.")

    @commands.command(name="adduser")
    async def adduser(self, ctx, user: commands.MemberConverter = None):
        miembro = ctx.author
        if not self.tiene_permiso(miembro):
            await ctx.send("🚫 No tienes permisos para añadir usuarios.")
            return

        canal_id = ctx.channel.id
        if canal_id not in usuarios_chat:
            await ctx.send("⚠️ No hay una conversación activa en este canal.")
            return

        if user is None:
            await ctx.send("❗ Menciona al usuario que quieres añadir.")
            return

        if canal_id not in usuarios_chat:
            usuarios_chat[canal_id] = set()
        usuarios_chat[canal_id].add(user.id)
        await ctx.send(f"✅ {user.mention} ha sido añadido a la conversación.")

    @commands.command(name="endchat")
    async def endchat(self, ctx):
        miembro = ctx.author
        if not self.tiene_permiso(miembro):
            await ctx.send("🚫 No tienes permisos para terminar la conversación.")
            return

        canal_id = ctx.channel.id
        if canal_id in usuarios_chat:
            del usuarios_chat[canal_id]
            await ctx.send("❌ Conversación con IA terminada. Hasta la próxima.")
        else:
            await ctx.send("⚠️ No hay una conversación activa en este canal.")

import asyncio

async def setup(bot):
    await bot.add_cog(ChatCommands(bot))
