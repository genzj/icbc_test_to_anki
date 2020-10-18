import coloredlogs

from .icbc_test_to_anki import main


if __name__ == '__main__':
    coloredlogs.install(level='INFO')
    main()
