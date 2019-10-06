from discord.ext.commands import when_mentioned_or


def custom_prefix(disco, message):
    guild_id = message.guild.id

    try:
        prefix = disco._prefixes[guild_id]
    except KeyError:
        guild = disco._guilds.get(guild_id)
        disco._prefixes[guild_id] = prefix = guild.data['options']['prefix']

    if prefix:
        return when_mentioned_or(prefix)(disco, message)

    return when_mentioned_or(*disco.prefixes)(disco, message)
