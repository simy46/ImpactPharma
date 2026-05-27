import os

from core.log_manager import LogManager
from retrieval.consts import LOG_DIR, is_pipeline_log
from retrieval.models import IterationSelection


class IterationSelector:
    def __init__(self, logger: LogManager, log_dir: str = LOG_DIR):
        self.logger = logger
        self.log_dir = log_dir

    def list_logs(self) -> list[str]:
        if not os.path.isdir(self.log_dir):
            raise FileNotFoundError(f"Log directory not found: {self.log_dir}")

        logs = [
            os.path.join(self.log_dir, filename)
            for filename in os.listdir(self.log_dir)
            if is_pipeline_log(filename)
        ]

        return sorted(logs)

    def select(self) -> IterationSelection:
        logs = self.list_logs()

        if not logs:
            raise RuntimeError(f"No pipeline logs found in {self.log_dir}")

        print("\nAvailable iterations:\n")

        for index, log_path in enumerate(logs, start=1):
            print(f"{index}. {log_path}")

        while True:
            raw_value = input("\nWhich iteration do you want to recover? ").strip()

            try:
                iteration_number = int(raw_value)
            except ValueError:
                print("Please enter a valid iteration number.")
                continue

            if 1 <= iteration_number <= len(logs):
                log_path = logs[iteration_number - 1]
                self.logger.write(
                    "info",
                    f"Selected recovery iteration {iteration_number}: {log_path}",
                )

                return IterationSelection(
                    iteration_number=iteration_number,
                    log_path=log_path,
                    all_logs=logs,
                )

            print(f"Please enter a number between 1 and {len(logs)}.")
