from client.core.config import Config
from client.core.storage import init_db
from client.core.cli import cli


def main():
    Config.init_paths()
    init_db()
    cli()

if __name__ == "__main__":
    main()