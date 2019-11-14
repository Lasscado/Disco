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
            if not ctx.gdb.options['dj_role']:
                raise commands.UserInputError()

            ctx.gdb.update({"options.dj_role": None})
            return await ctx.send(ctx.t('commands.djrole.reset', {"author": ctx.author.name,
                                                                  "emoji": self.disco.emoji["true"]}))

        ctx.gdb.update({"options.djRole": role.id})
        await ctx.send(ctx.t('commands.djrole.update', {"author": ctx.author.name,
                                                        "emoji": self.disco.emoji["true"], "role": role}))

    @commands.command(name='disablechannel', aliases=['dchannel'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_channels=True)
    async def _disable_channel(self, ctx, *, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel

        if channel.id in ctx.gdb.options['disabled_channels']:
            await ctx.gdb.pull({"options.disabled_channels": channel.id})
            await ctx.send(ctx.t('commands.disablechannel.allow', {"author": ctx.author.name,
                                                                   "emoji": self.disco.emoji["true"],
                                                                   "channel": channel.mention}))
        else:
            await ctx.gdb.push({"options.disabled_channels": channel.id})
            await ctx.send(ctx.t('commands.disablechannel.disallow', {"author": ctx.author.name,
                                                                      "emoji": self.disco.emoji["true"],
                                                                      "channel": channel.mention}))

    @commands.command(name='disablerole', aliases=['drole'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    async def _disable_role(self, ctx, *, role: discord.Role):
        if role >= ctx.author.top_role:
            return await ctx.send(ctx.t('commands.disablerole.higherRole', {
                "author": ctx.author.name, "emoji": self.disco.emoji["false"]}))

        if role.id in ctx.gdb.options['disabled_roles']:
            await ctx.gdb.pull({"options.disabled_roles": role.id})
            await ctx.send(ctx.t('commands.disablerole.enabled', {"role": role,
                                                                  "emoji": self.disco.emoji["true"],
                                                                  "author": ctx.author.name}))
        else:
            await ctx.gdb.push({"options.disabled_roles": role.id})
            await ctx.send(ctx.t('commands.disablerole.disabled', {"role": role,
                                                                   "emoji": self.disco.emoji["true"],
                                                                   "author": ctx.author.name}))

    @commands.command(name='localban', aliases=['lban'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, ban_members=True)
    async def _local_ban(self, ctx, *, member: discord.Member):
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(ctx.t('commands.localban.higherMember', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        if member.id in ctx.gdb.options['banned_members']:
            await ctx.gdb.pull({"options.banned_members": member.id})
            await ctx.send(ctx.t('commands.localban.unban', {"emoji": self.disco.emoji["true"],
                                                             "author": ctx.author.name, "member": member}))
        else:
            await ctx.gdb.push({"options.banned_members": member.id})
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
            return await ctx.send(ctx.t('commands.disablecommand.cantDisable', {"emoji": self.disco.emoji["false"],
                                                                                "author": ctx.author.name}))

        if command.name in ctx.gdb.options['disabled_commands']:
            await ctx.gdb.pull({"options.disabled_commands": command.name})
            await ctx.send(ctx.t('commands.disablecommand.enabled', {"command": command.name,
                                                                     "emoji": self.disco.emoji["true"],
                                                                     "author": ctx.author.name}))
        else:
            await ctx.gdb.push({"options.disabled_commands": command.name})
            await ctx.send(ctx.t('commands.disablecommand.disabled', {"command": command.name,
                                                                      "emoji": self.disco.emoji["true"],
                                                                      "author": ctx.author.name}))

    @commands.command(name='botchannel', aliases=['bch', 'botch'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, manage_channels=True)
    async def _bot_channel(self, ctx, *, channel: discord.TextChannel = None):
        if not channel:
            if not ctx.gdb.options['bot_channel']:
                raise commands.UserInputError()

            await ctx.gdb.set({"options.bot_channel": None})
            return await ctx.send(ctx.t('commands.botchannel.reset', {"author": ctx.author.name,
                                                                      "emoji": self.disco.emoji["true"]}))

        await ctx.gdb.set({"options.bot_channel": channel.id})
        await ctx.send(ctx.t('commands.botchannel.set', {"author": ctx.author.name,
                                                         "emoji": self.disco.emoji["true"],
                                                         "channel": channel.mention}))

    @commands.command(name='locale', aliases=['locales', 'language', 'lang', 'idioma', 'linguagem'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _locale(self, ctx, locale=None):
        locales = self.disco.i18n.strings.keys()

        if not locale or locale not in locales:
            available = ', '.join([f"**`{l}`**" for l in locales])

            return await ctx.send(ctx.t('commands.locale.invalid', {"available": available,
                                                                    "emoji": self.disco.emoji["false"],
                                                                    "author": ctx.author.name}))

        ctx.t = self.disco.i18n.get_t(locale)
        await ctx.gdb.set({"options.locale": locale})
        await ctx.send(ctx.t('commands.locale.success', {"locale": locale,
                                                         "emoji": self.disco.emoji["true"],
                                                         "author": ctx.author.name}))

        try:
            self.disco.wavelink.players[ctx.guild.id].t = ctx.t
        except KeyError:
            pass

    @commands.command(name='prefix', aliases=['setprefix'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _set_prefix(self, ctx, prefix=None):
        if not prefix:
            if not ctx.gdb.options['prefix']:
                raise commands.UserInputError

            await ctx.gdb.set({"options.prefix": None})
            self.disco._prefixes[ctx.guild.id] = None
            return await ctx.send(ctx.t('commands.prefix.reset', {"author": ctx.author.name,
                                                                  "emoji": self.disco.emoji["true"]}))

        if len(prefix) > 7:
            return await ctx.send(ctx.t('commands.prefix.invalid', {"author": ctx.author.name,
                                                                    "emoji": self.disco.emoji["false"]}))

        await ctx.gdb.set({"options.prefix": prefix})
        self.disco._prefixes[ctx.guild.id] = prefix
        await ctx.send(ctx.t('commands.prefix.success', {"author": ctx.author.name,
                                                         "emoji": self.disco.emoji["true"],
                                                         "prefix": prefix}))

    @commands.command(name='defaultvolume', aliases=['defaultvol', 'dvol'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _default_volume(self, ctx, vol: int = None):
        if not vol:
            if not ctx.gdb.options['default_volume']:
                raise commands.UserInputError

            await ctx.gdb.set({"options.default_volume": None})
            return await ctx.send(ctx.t('commands.defaultvolume.reset', {"author": ctx.author.name,
                                                                         "emoji": self.disco.emoji["true"]}))

        if not 0 < vol < 151:
            return await ctx.send(ctx.t('commands.defaultvolume.invalid', {"author": ctx.author.name,
                                                                           "emoji": self.disco.emoji["false"]}))

        await ctx.gdb.set({"options.default_volume": vol})
        await ctx.send(ctx.t('commands.defaultvolume.success', {"author": ctx.author.name,
                                                                "emoji": self.disco.emoji["true"],
                                                                "volume": vol}))

    @commands.command(name='modrole', aliases=['mrole', 'mr'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _mod_role(self, ctx, *, role: discord.Role = None):
        if role is None:
            if not ctx.gdb.options['mod_role']:
                raise commands.UserInputError

            await ctx.gdb.set({"options.mod_role": None})
            return await ctx.send(ctx.t('commands.modrole.reset', {"author": ctx.author.name,
                                                                   "emoji": self.disco.emoji["true"]}))

        await ctx.gdb.set({"options.mod_role": role.id})
        await ctx.send(ctx.t('commands.modrole.success', {"author": ctx.author.name,
                                                          "emoji": self.disco.emoji["true"],
                                                          "role": role.name}))

    @commands.command(name='modlogs', aliases=['modlog'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _mod_logs(self, ctx, *, channel: discord.TextChannel = None):
        if channel is None:
            if not ctx.gdb.options['mod_logs_channel']:
                raise commands.UserInputError

            await ctx.gdb.set({"options.mod_logs_channel": None})
            return await ctx.send(ctx.t('commands.modlogs.reset', {"author": ctx.author.name,
                                                                   "emoji": self.disco.emoji["true"]}))

        permissions = channel.permissions_for(ctx.me)
        missing = []
        emoji = self.disco.emoji["idle"]
        if not permissions.send_messages:
            missing.append(f'{emoji} **`{ctx.t("permissions.send_messages").upper()}`**')
        if not permissions.read_messages:
            missing.append(f'{emoji} **`{ctx.t("permissions.read_messages").upper()}`**')
        if not permissions.read_message_history:
            missing.append(f'{emoji} **`{ctx.t("permissions.read_message_history").upper()}`**')
        if not permissions.embed_links:
            missing.append(f'{emoji} **`{ctx.t("permissions.embed_links").upper()}`**')

        if missing:
            return await ctx.send(ctx.t('commands.modlogs.missingPermissions', {"emoji": self.disco.emoji["false"],
                                                                                "author": ctx.author.name,
                                                                                "channel": channel.mention,
                                                                                "permissions": '\n'.join(missing)}))

        await ctx.gdb.set({"options.mod_logs_channel": channel.id})
        await ctx.send(ctx.t('commands.modlogs.success', {"author": ctx.author.name,
                                                          "emoji": self.disco.emoji["true"],
                                                          "channel": channel.mention}))

    @commands.command(name='modthreshold', aliases=['modlimit', 'mthreshold', 'mlimit'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _mod_threshold(self, ctx, action, threshold: int = None):
        mod_threshold = ctx.gdb.options['mod_threshold']
        actions = mod_threshold.keys()
        if action not in actions:
            return await ctx.send(ctx.t('commands.modthreshold.invalidAction', {"emoji": self.disco.emoji["false"],
                                                                                "author": ctx.author.name,
                                                                                "actions": ', '.join(f'**`{a}`**'
                                                                                                     for a in actions)
                                                                                }))

        if threshold is None:
            if mod_threshold[action] is None:
                raise commands.MissingRequiredArgument

            await ctx.gdb.set({f"options.mod_threshold.{action}": None})
            return await ctx.send(ctx.t('commands.modthreshold.reset', {"emoji": self.disco.emoji["true"],
                                                                        "author": ctx.author.name,
                                                                        "action": action}))

        if not 0 < threshold < 1001:
            return await ctx.send(ctx.t('commands.modthreshold.invalidThreshold', {"emoji": self.disco.emoji["false"],
                                                                                   "author": ctx.author.name}))

        await ctx.gdb.set({f"options.mod_threshold.{action}": threshold})
        await ctx.send(ctx.t('commands.modthreshold.success', {"emoji": self.disco.emoji["true"],
                                                               "author": ctx.author.name,
                                                               "action": action,
                                                               "threshold": threshold}))

    @commands.command(name='messagelogs', aliases=['messagelog'])
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _message_logs(self, ctx, *, channel: discord.TextChannel):
        if channel is None:
            if not ctx.gdb.options['message_logs_channel']:
                raise commands.UserInputError

            await ctx.gdb.set({"options.message_logs_channel": None})
            return await ctx.send(ctx.t('commands.messagelogs.reset', {"author": ctx.author.name,
                                                                       "emoji": self.disco.emoji["true"]}))

        permissions = channel.permissions_for(ctx.me)
        missing = []
        emoji = self.disco.emoji["idle"]
        if not permissions.send_messages:
            missing.append(f'{emoji} **`{ctx.t("permissions.send_messages").upper()}`**')
        if not permissions.read_messages:
            missing.append(f'{emoji} **`{ctx.t("permissions.read_messages").upper()}`**')
        if not permissions.read_message_history:
            missing.append(f'{emoji} **`{ctx.t("permissions.read_message_history").upper()}`**')
        if not permissions.embed_links:
            missing.append(f'{emoji} **`{ctx.t("permissions.embed_links").upper()}`**')

        if missing:
            return await ctx.send(ctx.t('commands.messagelogs.missingPermissions', {"emoji": self.disco.emoji["false"],
                                                                                    "author": ctx.author.name,
                                                                                    "channel": channel.mention,
                                                                                    "permissions": '\n'.join(missing)}))

        await ctx.gdb.set({"options.message_logs_channel": channel.id})
        await ctx.send(ctx.t('commands.messagelogs.success', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["true"],
                                                              "channel": channel.mention}))


def setup(disco):
    disco.add_cog(Admin(disco))
