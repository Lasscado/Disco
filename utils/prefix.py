from discord.ext.commands import when_mentioned_or


async def custom_prefix(disco, message):
    guild_id = message.guild.id

    try:
        prefix = disco._prefixes[guild_id]
    except KeyError:
        guild = await disco.db.get_guild(guild_id)
        disco._prefixes[guild_id] = prefix = guild.options['prefix']

    return when_mentioned_or(prefix)(disco, message) if prefix else when_mentioned_or(*disco.prefixes)(disco, message)
