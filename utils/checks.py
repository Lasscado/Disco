from discord.ext import commands

import discord

class Checks:
    @staticmethod
    def staffer_or_dj_role():
        async def predicate(ctx):
            role = ctx.guild.get_role(ctx._guild.data['options']['djRole'])
            if ctx.author.guild_permissions.manage_guild or role in ctx.author.roles:
                return True

            raise commands.errors.MissingRole([role])

        return commands.check(predicate)