from discord.ext import commands

import discord

class Checks:
    @staticmethod
    def staffer_or_role(name):
        async def predicate(ctx):
            role = discord.utils.find(lambda r: r.name.lower() == name.lower(), ctx.guild.roles)
            if ctx.author.guild_permissions.manage_guild or role in ctx.author.roles:
                return True

            raise commands.errors.MissingRole([role])

        return commands.check(predicate)