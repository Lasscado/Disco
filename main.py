from coloredlogs import install
from lite import DiscoLite

if __name__ == '__main__':
    install(level=20)
    DiscoLite().run()
