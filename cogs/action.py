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
    async def _kiss(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
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
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='stare')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _stare(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.stare.noMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.stare.selfMention', {"emoji": self.disco.emoji["false"],
                                                                       "author": ctx.author.name}))

        image = await self.weeb.random_image('stare')
        emoji = random_choice(self.disco.emoji['stare'])
        phrase = random_choice(ctx.t('commands.stare.withReason' if reason else 'commands.stare.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='hug')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _hug(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.hug.noMention', {"emoji": self.disco.emoji["false"],
                                                                   "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.hug.selfMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        image = await self.weeb.random_image('hug')
        emoji = random_choice(self.disco.emoji['hug'])
        phrase = random_choice(ctx.t('commands.hug.withReason' if reason else 'commands.hug.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='pat')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _pat(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.pat.noMention', {"emoji": self.disco.emoji["false"],
                                                                   "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.pat.selfMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        image = await self.weeb.random_image('pat')
        emoji = random_choice(self.disco.emoji['pat'])
        phrase = random_choice(ctx.t('commands.pat.withReason' if reason else 'commands.pat.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='slap')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _slap(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.slap.noMention', {"emoji": self.disco.emoji["false"],
                                                                    "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.slap.selfMention', {"emoji": self.disco.emoji["false"],
                                                                      "author": ctx.author.name}))

        if ctx.me in members:
            return await ctx.send(ctx.t('commands.slap.botMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        image = await self.weeb.random_image('slap')
        emoji = random_choice(self.disco.emoji['slap'])
        phrase = random_choice(ctx.t('commands.slap.withReason' if reason else 'commands.slap.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='lick')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _lick(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.lick.noMention', {"emoji": self.disco.emoji["false"],
                                                                    "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.lick.selfMention', {"emoji": self.disco.emoji["false"],
                                                                      "author": ctx.author.name}))

        if ctx.me in members:
            return await ctx.send(ctx.t('commands.lick.botMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        image = await self.weeb.random_image('lick')
        emoji = random_choice(self.disco.emoji['lick'])
        phrase = random_choice(ctx.t('commands.lick.withReason' if reason else 'commands.lick.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='tickle')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _tickle(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.tickle.noMention', {"emoji": self.disco.emoji["false"],
                                                                      "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.tickle.selfMention', {"emoji": self.disco.emoji["false"],
                                                                        "author": ctx.author.name}))

        image = await self.weeb.random_image('tickle')
        emoji = random_choice(self.disco.emoji['tickle'])
        phrase = random_choice(ctx.t('commands.tickle.withReason' if reason else 'commands.tickle.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='bite')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _bite(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.bite.noMention', {"emoji": self.disco.emoji["false"],
                                                                    "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.bite.selfMention', {"emoji": self.disco.emoji["false"],
                                                                      "author": ctx.author.name}))

        if ctx.me in members:
            return await ctx.send(ctx.t('commands.bite.botMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        image = await self.weeb.random_image('bite')
        emoji = random_choice(self.disco.emoji['bite'])
        phrase = random_choice(ctx.t('commands.bite.withReason' if reason else 'commands.bite.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='greet')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _greet(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.greet.noMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.greet.selfMention', {"emoji": self.disco.emoji["false"],
                                                                       "author": ctx.author.name}))

        image = await self.weeb.random_image('greet')
        emoji = random_choice(self.disco.emoji['greet'])
        phrase = random_choice(ctx.t('commands.greet.withReason' if reason else 'commands.greet.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='smile')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _smile(self, ctx, members: commands.Greedy[discord.Member], *, reason: commands.clean_content = ''):
        if not members:
            return await ctx.send(ctx.t('commands.smile.noMention', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))

        if ctx.author in members:
            return await ctx.send(ctx.t('commands.smile.selfMention', {"emoji": self.disco.emoji["false"],
                                                                       "author": ctx.author.name}))

        image = await self.weeb.random_image('smile')
        emoji = random_choice(self.disco.emoji['smile'])
        phrase = random_choice(ctx.t('commands.smile.withReason' if reason else 'commands.smile.noReason')).format(
            author=ctx.author.name, members=', '.join(f'**{m.name}**' for m in list(set(members))[:3]),
            reason=reason[:1500],
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)

    @commands.command(name='cry')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _cry(self, ctx, *, reason: commands.clean_content = ''):
        image = await self.weeb.random_image('cry')
        emoji = random_choice(self.disco.emoji['cry'])
        phrase = random_choice(ctx.t('commands.cry.withReason' if reason else 'commands.cry.noReason')).format(
            author=ctx.author.name, reason=reason[:1500]
        )

        em = discord.Embed(
            colour=random_color()
        ).set_image(
            url=image.url
        ).set_footer(
            text=f'{ctx.author} | Powered by Weeb.sh'
        )

        await ctx.send(content=f'{emoji} | {phrase}', embed=em)


def setup(disco):
    disco.add_cog(Action(disco))
