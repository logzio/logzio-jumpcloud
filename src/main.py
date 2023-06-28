from manager import Manager
from logging.config import fileConfig


if __name__ == '__main__':
    manager = Manager()
    fileConfig('src/logging_config.ini', disable_existing_loggers=False)
    manager.run()