from core.config import Config
from core.storage import init_db
from core.cli import cli


def main():
    Config.init_paths()
    init_db()
    cli()

if __name__ == "__main__":
    main()