from discord.ext import commands
from utils import checks

import discord

class Admin(commands.Cog):
    def __init__(self, lite):
        self.lite = lite

    @commands.command(name='djrole', aliases=['djr'], usage='<@Menção|Nome|ID>',
        description='Define o cargo DJ no servidor.')
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _dj_role(self, ctx, *, role: discord.Role = None):
        if not role:
            if not ctx._guild.data['options']['djRole']:
                raise commands.UserInputError()

            ctx._guild.update({"options.djRole": None})
            return await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você resetou'
                ' o **`Cargo DJ`** desse servidor.')

        ctx._guild.update({"options.djRole": role.id})
        await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você definiu o cargo **'
            f'`{role}`** como `Cargo DJ`.')

    @commands.command(name='disablechannel', aliases=['dchannel'], usage='<#Menção|Nome|ID>',
        description='Desativa ou ativa um canal em que o Bot possa ser usado.')
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _disable_channel(self, ctx, *, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel

        if channel.id in ctx._guild.data['options']['disabledChannels']:
            ctx._guild.remove({"options.disabledChannels": channel.id})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você me permitiu ser '
                f'usado no canal {channel.mention}.')
        else:
            ctx._guild.insert({"options.disabledChannels": channel.id})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você me proibiu de '
                f'ser usado no canal {channel.mention}.')

    @commands.command(name='disablerole', aliases=['drole'], usage='<@Menção|Nome|ID>',
        description='Permite ou proíbe membros com um cargo específico de usarem o Bot.')
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def _disable_role(self, ctx, *, role: discord.Role):
        if role >= ctx.author.top_role:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você não '
                'pode desativar um cargo que seja igual ou maior que o seu cargo mais alto.')

        if role.id in ctx._guild.data['options']['disabledRoles']:
            ctx._guild.remove({"options.disabledRoles": role.id})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você me permitiu ser '
                f'usado por membros com o cargo **`{role}`**.')
        else:
            ctx._guild.insert({"options.disabledRoles": role.id})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você me proibiu de '
                f'ser usado por membros com o cargo **`{role}`**.')

    @commands.command(name='localban', aliases=['lban'], usage='<@Menção|Nome|ID>',
        description='Permite ou proíbe um membro de usar o Bot nesse servidor.')
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, ban_members=True)
    async def _local_ban(self, ctx, *, member: discord.Member):
        if member.top_role >= ctx.author.top_role:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você não '
                'pode fazer um banimento local em um membro que possua direitos equivalentes ou '
                'maiores que o seu.')

        if member.id in ctx._guild.data['options']['bannedMembers']:
            ctx._guild.remove({"options.bannedMembers": member.id})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você me permitiu ser '
                f'usado pelo membro **`{member}`** nesse servidor.')
        else:
            ctx._guild.insert({"options.bannedMembers": member.id})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você me proibiu de '
                f'ser usado pelo membro **`{member}`** nesse servidor.')

    @commands.command(name='disablecommand', aliases=['dcmd'], usage='<Nome>',
        description='Permite ou proíbe que um comando específico seja usado nesse servidor.')
    @commands.cooldown(1, 8, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True, ban_members=True)
    async def _disable_command(self, ctx, command):
        command = self.lite.get_command(command)
        if not command:
            raise commands.UserInputError()

        if command.cog_name in ['Admin', 'Owner']:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você não '
                'pode desativar esse comando.')

        if command.name in ctx._guild.data['options']['disabledCommands']:
            ctx._guild.remove({"options.disabledCommands": command.name})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você permitiu o uso '
                f'do comando **`{command}`** nesse servidor.')
        else:
            ctx._guild.insert({"options.disabledCommands": command.name})
            await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você proibiu o uso '
                f'do comando **`{command}`** nesse servidor.')

def setup(lite):
    lite.add_cog(Admin(lite))