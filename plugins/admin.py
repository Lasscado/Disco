import discord
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

    @commands.command(name='djrole', aliases=['djr'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _dj_role(self, ctx, *, role: discord.Role = None):
        if not role:
            if not ctx._guild.data['options']['djRole']:
                raise commands.UserInputError()

            ctx._guild.update({"options.djRole": None})
            return await ctx.send(ctx.t('commands.djrole.reset', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"]}))

        ctx._guild.update({"options.djRole": role.id})
        await ctx.send(ctx.t('commands.djrole.update', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"], "role": role}))

    @commands.command(name='disablechannel', aliases=['dchannel'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_channels=True)
    async def _disable_channel(self, ctx, *, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel

        if channel.id in ctx._guild.data['options']['disabledChannels']:
            ctx._guild.remove({"options.disabledChannels": channel.id})
            await ctx.send(ctx.t('commands.disablechannel.allow', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"], "channel": channel.mention}))
        else:
            ctx._guild.insert({"options.disabledChannels": channel.id})
            await ctx.send(ctx.t('commands.disablechannel.disallow', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"], "channel": channel.mention}))

    @commands.command(name='disablerole', aliases=['drole'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    async def _disable_role(self, ctx, *, role: discord.Role):
        if role >= ctx.author.top_role:
            return await ctx.send(ctx.t('commands.disablerole.higherRole', {
                "author": ctx.author.name, "emoji": self.disco.emoji["false"]}))

        if role.id in ctx._guild.data['options']['disabledRoles']:
            ctx._guild.remove({"options.disabledRoles": role.id})
            await ctx.send(ctx.t('commands.disablerole.enabled', {"role": role,
                "emoji": self.disco.emoji["true"], "author": ctx.author.name}))
        else:
            ctx._guild.insert({"options.disabledRoles": role.id})
            await ctx.send(ctx.t('commands.disablerole.disabled', {"role": role,
                "emoji": self.disco.emoji["true"], "author": ctx.author.name}))

    @commands.command(name='localban', aliases=['lban'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, ban_members=True)
    async def _local_ban(self, ctx, *, member: discord.Member):
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(ctx.t('commands.localban.higherMember', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        if member.id in ctx._guild.data['options']['bannedMembers']:
            ctx._guild.remove({"options.bannedMembers": member.id})
            await ctx.send(ctx.t('commands.localban.unban', {"emoji": self.disco.emoji["true"],
                "author": ctx.author.name, "member": member}))
        else:
            ctx._guild.insert({"options.bannedMembers": member.id})
            await ctx.send(ctx.t('commands.localban.ban', {"emoji": self.disco.emoji["true"],
                "author": ctx.author.name, "member": member}))

    @commands.command(name='disablecommand', aliases=['dcmd'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _disable_command(self, ctx, command):
        command = self.disco.get_command(command)
        if not command:
            raise commands.UserInputError()

        if command.cog_name in ['Admin', 'Owner']:
            return await ctx.send(ctx.t('commands.disablecommand.cantDisable', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        if command.name in ctx._guild.data['options']['disabledCommands']:
            ctx._guild.remove({"options.disabledCommands": command.name})
            await ctx.send(ctx.t('commands.disablecommand.enabled', {"command": command.name,
                "emoji": self.disco.emoji["true"], "author": ctx.author.name}))
        else:
            ctx._guild.insert({"options.disabledCommands": command.name})
            await ctx.send(ctx.t('commands.disablecommand.disabled', {"command": command.name,
                "emoji": self.disco.emoji["true"], "author": ctx.author.name}))

    @commands.command(name='botchannel', aliases=['bch', 'botch'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_channels=True)
    async def _bot_channel(self, ctx, *, channel: discord.TextChannel = None):
        if not channel:
            if not ctx._guild.data['options']['botChannel']:
                raise commands.UserInputError()

            ctx._guild.update({"options.botChannel": None})
            return await ctx.send(ctx.t('commands.botchannel.reset', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"]}))

        ctx._guild.update({"options.botChannel": channel.id})
        await ctx.send(ctx.t('commands.botchannel.set', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"], "channel": channel.mention}))

    @commands.command(name='locale', aliases=['locales', 'language', 'lang', 'idioma', 'linguagem'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _locale(self, ctx, locale = None):
        locales = self.disco.i18n.strings.keys()

        if not locale or locale not in locales:
            available = ', '.join([f"**`{l}`**" for l in locales])

            return await ctx.send(ctx.t('commands.locale.invalid', {"available": available,
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        ctx.t = self.disco.i18n.get_t(locale)
        ctx._guild.update({"options.locale": locale})
        await ctx.send(ctx.t('commands.locale.success', {"locale": locale,
                "emoji": self.disco.emoji["true"], "author": ctx.author.name}))

        try:
            self.disco.wavelink.players[ctx.guild.id].t = ctx.t
        except KeyError:
            pass

    @commands.command(name='prefix', aliases=['setprefix'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _set_prefix(self, ctx, prefix = None):
        if not prefix:
            if not ctx._guild.data['options']['prefix']:
                raise commands.UserInputError

            ctx._guild.update({"options.prefix": None})
            self.disco._prefixes[ctx.guild.id] = None
            return await ctx.send(ctx.t('commands.prefix.reset', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"]}))

        if len(prefix) > 7:
            return await ctx.send(ctx.t('commands.prefix.invalid', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        ctx._guild.update({"options.prefix": prefix})
        self.disco._prefixes[ctx.guild.id] = prefix
        await ctx.send(ctx.t('commands.prefix.success', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"], "prefix": prefix}))

    @commands.command(name='defaultvolume', aliases=['defaultvol', 'dvol'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _default_volume(self, ctx, vol: int = None):
        if not vol:
            if not ctx._guild.data['options']['defaultVolume']:
                raise commands.UserInputError

            ctx._guild.update({"options.defaultVolume": None})
            return await ctx.send(ctx.t('commands.defaultvolume.reset', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"]}))

        if not 0 < vol < 151:
            return await ctx.send(ctx.t('commands.defaultvolume.invalid', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        ctx._guild.update({"options.defaultVolume": vol})
        await ctx.send(ctx.t('commands.defaultvolume.success', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"], "volume": vol}))


def setup(disco):
    disco.add_cog(Admin(disco))