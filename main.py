from coloredlogs import install
from disco import Disco

if __name__ == '__main__':
    install(level=20)
    Disco('Kotori').run()