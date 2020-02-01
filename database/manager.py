from datetime import datetime, timedelta

from motor import motor_asyncio

from .models import DiscoBan, DiscoGuild, DiscoModLog, DiscoShard, DiscoMessage


class DatabaseManager:
    def __init__(self, name, uri):
        self._client = motor_asyncio.AsyncIOMotorClient(uri)
        self._db = db = self._client[name]
        self._bans = db.bans
        self._guilds = db.guilds
        self._shards = db.shards
        self._mod_logs = db.mod_logs
        self._messages = db.messages

    @property
    async def total_bans(self):
        return await self._bans.count_documents({})

    @property
    async def total_shards(self):
        return await self._shards.count_documents({})

    @property
    async def total_messages(self):
        return await self._messages.count_documents({})

    async def total_mod_logs(self, guild_id):
        return await self._mod_logs.count_documents({"guild_id": guild_id})

    async def total_daily_mod_logs(self, action, guild_id, moderator_id):
        return await self._mod_logs.count_documents({"action": action, "guild_id": guild_id,
                                                     "moderator_id": moderator_id,
                                                     "date": {
                                                         "$gt": (datetime.utcnow() - timedelta(days=1)).timestamp()
                                                     }})

    async def connect(self):
        await self._db.command('ping')

    async def get_guild(self, guild_id, register=True):
        if data := await self._guilds.find_one({"_id": guild_id}):
            return DiscoGuild(data, self._guilds)
        elif register:
            return await self.register_guild(guild_id)

    async def get_bans(self, **kwargs):
        return [DiscoBan(data, self._bans) async for data in self._bans.find(kwargs)]

    async def get_last_ban(self, **kwargs):
        if data := await self._bans.find(kwargs).sort('date', -1).limit(1).to_list(None):
            return DiscoBan(data[0], self._bans)

    async def get_first_ban(self, **kwargs):
        if data := await self._bans.find(kwargs).sort('date', 1).limit(1).to_list(None):
            return DiscoBan(data[0], self._bans)

    async def get_shards(self, **kwargs):
        return [DiscoShard(data, self._shards) async for data in self._shards.find(kwargs)]

    async def get_shard(self, shard_id, register=True):
        if data := await self._shards.find_one({"_id": shard_id}):
            return DiscoShard(data, self._shards)
        elif register:
            return await self.register_shard(shard_id)

    async def get_mod_log(self, **kwargs):
        if data := await self._mod_logs.find_one(kwargs):
            return DiscoModLog(data)

    async def get_last_mod_log(self, **kwargs):
        if data := await self._mod_logs.find(kwargs).sort('date', -1).limit(1).to_list(None):
            return DiscoModLog(data[0])

    async def get_message(self, message_id):
        if data := await self._messages.find_one({"_id": message_id}):
            return DiscoMessage(data, self._messages)

    async def get_messages(self, messages_id):
        return [DiscoMessage(data, self._messages) async for data in self._messages.find({"_id": {"$in": messages_id}})]

    async def delete_messages_days(self, days):
        timestamp = (datetime.utcnow() - timedelta(days=days)).timestamp()
        return (await self._messages.delete_many({"timestamp": {"$lte": timestamp}})).deleted_count

    async def register_guild(self, guild_id):
        data = {
            "_id": guild_id,
            "options": {
                "locale": "en_US",
                "prefix": None,
                "dj_role": None,
                "auto_role": None,
                "mod_role": None,
                "mod_logs_channel": None,
                "bot_channel": None,
                "message_logs_channel": None,
                "member_logs_channel": None,
                "default_volume": None,
                "mod_threshold": {
                    "ban": None,
                    "kick": None,
                    "softban": None,
                    "unban": None,
                    "clean": None
                },
                "disabled_commands": [],
                "disabled_channels": [],
                "disabled_roles": [],
                "banned_members": []
            }
        }

        await self._guilds.insert_one(data)

        return DiscoGuild(data, self._guilds)

    async def register_ban(self, target_id, author_id, is_guild, reason):
        data = {
            "target_id": target_id,
            "author_id": author_id,
            "is_guild": is_guild,
            "reason": reason,
            "date": datetime.utcnow().timestamp(),
            "ignore": False,
            "ignored_at": None
        }

        await self._bans.insert_one(data)

        return DiscoBan(data, self._bans)

    async def register_shard(self, shard_id):
        data = {
            "_id": shard_id,
            "created_at": datetime.utcnow().timestamp(),
            "launched_at": None,
            "last_update": None,
            "latency": 0,
            "guilds": 0,
            "members": 0,
            "players": 0
        }

        await self._shards.insert_one(data)

        return DiscoShard(data, self._shards)

    async def register_mod_log(self, action, case_id, moderator_id, guild_id, channel_id, message_id):
        data = {
            "action": action,
            "case_id": case_id,
            "moderator_id": moderator_id,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "message_id": message_id,
            "date": datetime.utcnow().timestamp()
        }

        await self._mod_logs.insert_one(data)

        return DiscoModLog(data)

    async def register_message(self, message):
        data = {
            "_id": message.id,
            "author_id": message.author.id,
            "channel_id": message.channel.id,
            "guild_id": message.guild.id,
            "content": message.content or ('\n'.join(attachment.proxy_url for attachment in message.attachments)
                                           if message.attachments else ''),
            "timestamp": message.created_at.timestamp()
        }

        await self._messages.insert_one(data)

        return DiscoMessage(data, self._messages)
