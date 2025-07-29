from discord.ext import commands
import discord

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🛠 Comandos disponibles",
            description="Aquí tienes una lista de comandos:",
            color=0x00ffcc
        )
        embed.add_field(name="?startchat", value="Inicia una conversación con el bot.", inline=False)
        embed.add_field(name="?adduser", value="Agrega un usuario a la conversación.", inline=False)
        embed.add_field(name="?endchat", value="Finaliza la conversación activa.", inline=False)
            # Se elimina el texto del pie de página según solicitud
            # embed.set_footer(text="Usa ?comando para más información.")
        await ctx.send(embed=embed)

import asyncio

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
