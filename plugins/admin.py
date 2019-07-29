from discord.ext import commands
from os import listdir
from utils import l

import discord
import re

LOCALE = re.compile('[a-z]{2}-[A-Z]{2}$')

class Admin(commands.Cog):
    def __init__(self, lite):
        self.lite = lite

    @commands.command(name='djrole', aliases=['djr'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _dj_role(self, ctx, *, role: discord.Role = None):
        if not role:
            if not ctx._guild.data['options']['djRole']:
                raise commands.UserInputError()

            ctx._guild.update({"options.djRole": None})
            return await ctx.send(l(ctx, 'commands.djrole.reset') % (
                self.lite.emoji["true"], ctx.author.name))

        ctx._guild.update({"options.djRole": role.id})
        await ctx.send(l(ctx, 'commands.djrole.update') % (
                self.lite.emoji["true"], ctx.author.name, role))

    @commands.command(name='disablechannel', aliases=['dchannel'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_channels=True)
    async def _disable_channel(self, ctx, *, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel

        if channel.id in ctx._guild.data['options']['disabledChannels']:
            ctx._guild.remove({"options.disabledChannels": channel.id})
            await ctx.send(l(ctx, 'commands.disablechannel.allow') % (
                self.lite.emoji["true"], ctx.author.name, channel.mention))
        else:
            ctx._guild.insert({"options.disabledChannels": channel.id})
            await ctx.send(l(ctx, 'commands.disablechannel.disallow') % (
                self.lite.emoji["true"], ctx.author.name, channel.mention))

    @commands.command(name='disablerole', aliases=['drole'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    async def _disable_role(self, ctx, *, role: discord.Role):
        if role >= ctx.author.top_role:
            return await ctx.send(l(ctx, 'commands.disablerole.higherRole') % (
                self.lite.emoji["false"], ctx.author.name))

        if role.id in ctx._guild.data['options']['disabledRoles']:
            ctx._guild.remove({"options.disabledRoles": role.id})
            await ctx.send(l(ctx, 'commands.disablerole.enabled') % (
                self.lite.emoji["true"], ctx.author.name, role))
        else:
            ctx._guild.insert({"options.disabledRoles": role.id})
            await ctx.send(l(ctx, 'commands.disablerole.disabled') % (
                self.lite.emoji["true"], ctx.author.name, role))

    @commands.command(name='localban', aliases=['lban'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, ban_members=True)
    async def _local_ban(self, ctx, *, member: discord.Member):
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(l(ctx, 'commands.localban.higherMember') % (
                self.lite.emoji["false"], ctx.author.name))

        if member.id in ctx._guild.data['options']['bannedMembers']:
            ctx._guild.remove({"options.bannedMembers": member.id})
            await ctx.send(l(ctx, 'commands.localban.unban') % (
                self.lite.emoji["true"], ctx.author.name, member))
        else:
            ctx._guild.insert({"options.bannedMembers": member.id})
            await ctx.send(l(ctx, 'commands.localban.ban') % (
                self.lite.emoji["true"], ctx.author.name, member))

    @commands.command(name='disablecommand', aliases=['dcmd'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _disable_command(self, ctx, command):
        command = self.lite.get_command(command)
        if not command:
            raise commands.UserInputError()

        if command.cog_name in ['Admin', 'Owner']:
            return await ctx.send(l(ctx, 'commands.disablecommand.cantDisable') % (
                self.lite.emoji["false"], ctx.author.name))

        if command.name in ctx._guild.data['options']['disabledCommands']:
            ctx._guild.remove({"options.disabledCommands": command.name})
            await ctx.send(l(ctx, 'commands.disablecommand.enabled') % (
                self.lite.emoji["true"], ctx.author.name, command))
        else:
            ctx._guild.insert({"options.disabledCommands": command.name})
            await ctx.send(l(ctx, 'commands.disablecommand.disabled') % (
                self.lite.emoji["true"], ctx.author.name, command))

    @commands.command(name='botchannel', aliases=['bch', 'botch'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_channels=True)
    async def _bot_channel(self, ctx, *, channel: discord.TextChannel = None):
        if not channel:
            if not ctx._guild.data['options']['botChannel']:
                raise commands.UserInputError()

            ctx._guild.update({"options.botChannel": None})
            return await ctx.send(l(ctx, 'commands.botchannel.reset') % (
                self.lite.emoji["true"], ctx.author.name))

        ctx._guild.update({"options.botChannel": channel.id})
        await ctx.send(l(ctx, 'commands.botchannel.set') % (
            self.lite.emoji["true"], ctx.author.name, channel.mention))

    @commands.command(name='language', aliases=['locale', 'lang', 'idioma', 'linguagem'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _language(self, ctx, locale = None):
        locales = [l for l in listdir('./locales') if LOCALE.match(l)]

        if not locale or locale not in locales:
            available = ', '.join([f"**`{l}`**" for l in listdir('./locales')])

            return await ctx.send(l(ctx, 'commands.language.invalid') % (self.lite.emoji["false"],
                ctx.author.name, available))

        ctx._guild.update({"options.locale": locale})
        await ctx.send(l(locale, 'commands.language.success') % (self.lite.emoji["true"],
            ctx.author.name, locale))

def setup(lite):
    lite.add_cog(Admin(lite))