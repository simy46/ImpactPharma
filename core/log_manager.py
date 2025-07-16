import os
import logging
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_timestamped_log_file():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"pipeline_{timestamp}.log")

class LogManager:
    def __init__(self, name: str = "pipeline"):
        self.log_path = get_timestamped_log_file()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        if not self.logger.handlers:
            formatter = logging.Formatter("%(message)s")

            file_handler = logging.FileHandler(self.log_path, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

    def write(self, type_: str, message: str) -> None:
        print(f"[{type_.upper()}] {message}")
        level_map = {
            "info": self.logger.info,
            "success": self.logger.info,
            "token": self.logger.debug,
            "wait": self.logger.debug,
            "warn": self.logger.warning,
            "error": self.logger.error,
        }
        log_func = level_map.get(type_.lower(), self.logger.info)
        log_func(f"[{type_.upper()}] {message}")
