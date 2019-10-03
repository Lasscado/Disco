from discord.ext.commands.errors import CommandError


class MusicError(CommandError):
    '''Erro padrão para o módulo de Música'''
    pass


class WaitingForPreviousChoice(CommandError):
    pass
