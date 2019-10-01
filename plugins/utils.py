import discord
from discord.ext import commands

from utils import l


class Utils(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

    @commands.command(name='avatar', aliases=['av', 'pfp', 'picture'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _avatar(self, ctx, *, member: discord.Member = None):
        if not member:
            member = ctx.author

        em = discord.Embed(
            colour=member.colour if member.colour.value else self.disco.color[0],
            description=l(ctx, 'commands.avatar.clickToDownload', {
                "url": member.avatar_url
            })
        ).set_author(
            name=l(ctx, 'commands.avatar.memberAvatar', {"member": member}),
            icon_url=member.avatar_url
        ).set_image(
            url=member.avatar_url
        ).set_footer(
            text=str(ctx.author)
        )

        await ctx.send(embed=em)


def setup(disco):
    disco.add_cog(Utils(disco))
