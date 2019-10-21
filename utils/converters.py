import re
from datetime import timedelta

from discord.ext.commands import Converter

TIME_REGEX = re.compile('(?:([0-9]+)d ?)?(?:([0-9]+)h ?)?(?:([0-9]+)m ?)?(?:([0-9]+)s)?')


class TimeConverter(Converter):
    async def convert(self, ctx, argument):
        if match := TIME_REGEX.match(argument):
            return (timedelta(days=int(match.group(1) or 0), hours=int(match.group(2) or 0),
                              minutes=int(match.group(3) or 0), seconds=int(match.group(4) or 0)),
                    argument[len(match.group(0)):])

        return None, argument
