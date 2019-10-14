from random import choice as random_choice
from os import environ

import weeb
import discord
from discord.ext import commands

from utils import random_color


class Action(commands.Cog):
    def __init__(self, disco):
        self.disco = disco
        self.weeb = weeb.Client(token=environ['WEEB_SERVICES_API_TOKEN'],
                                user_agent='Disco/3.2.1')

    @commands.command(name='kiss')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _kiss(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        if not members:
            return await ctx.send(ctx.t('commands.kiss.noMention', {"emoji": self.disco.emoji["false"],
                                                                    "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.kiss.selfMention', {"emoji": self.disco.emoji["false"],
                                                                      "author": ctx.author.name}))

        if ctx.me in members:
            return await ctx.send(ctx.t('commands.kiss.botMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        image = await self.weeb.random_image('kiss')
        emoji = random_choice(self.disco.emoji['kiss'])
        phrase = random_choice(ctx.t('commands.kiss.withReason' if reason else 'commands.kiss.noReason')).format(
            author=ctx.author.display_name, members=', '.join(f'**{m.display_name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} {phrase}', embed=em)


def setup(disco):
    disco.add_cog(Action(disco))
