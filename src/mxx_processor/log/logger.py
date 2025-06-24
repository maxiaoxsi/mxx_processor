import time
import datetime

class logger:
    def __init__(self, path_log) -> None:
        self._path_log = path_log

    def warning(self, str_log):
        with open(self._path_log, 'a') as f:
            time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{time_str}] warning: {str_log}\n")