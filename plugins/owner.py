from discord.ext import commands

import re
import os
import sys
import discord

class Owner(commands.Cog):
    def __init__(self, lite):
        self.lite = lite

    @commands.command(name='eval', hidden=True)
    @commands.is_owner()
    async def _eval(self, ctx, *, code):
        try:
            if code.startswith('await '):
                code = await eval(code[6:])
            else:
                code = eval(code)
        
            await ctx.send(f'```py\n{code}```')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')

    @commands.command(name='reload', aliases=['rl'], hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx, plugin):
        try:
            self.lite.reload_extension('plugins.' + plugin)
            await ctx.message.add_reaction('<:discoTrue:512912547108749312>')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')
            await ctx.message.add_reaction('<:discoFalse:512912546869673999>')

    @commands.command(name='load', aliases=['ld'], hidden=True)
    @commands.is_owner()
    async def _load(self, ctx, plugin):
        try:
            self.lite.load_extension('plugins.' + plugin)
            await ctx.message.add_reaction('<:discoTrue:512912547108749312>')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')
            await ctx.message.add_reaction('<:discoFalse:512912546869673999>')

    @commands.command(name='unload', aliases=['ul'], hidden=True)
    @commands.is_owner()
    async def _unload(self, ctx, plugin):
        try:
            self.lite.unload_extension('plugins.' + plugin)
            await ctx.message.add_reaction('<:discoTrue:512912547108749312>')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')
            await ctx.message.add_reaction('<:discoFalse:512912546869673999>')

def setup(lite):
    lite.add_cog(Owner(lite))