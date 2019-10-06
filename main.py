import coloredlogs
from dotenv import load_dotenv

load_dotenv()

from disco import Disco

if __name__ == '__main__':
    coloredlogs.install(level=20)
    Disco().run()
