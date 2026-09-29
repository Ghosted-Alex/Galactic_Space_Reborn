"""The module for logging into logs"""

import logging

# 1. Define ANSI Color Codes
class LogColors:
    RESET = "\033[0m"
    GRAY = "\033[90m"      # DEBUG
    GREEN = "\033[32m"     # INFO (20)
    YELLOW = "\033[33m"    # WARNING (30)
    RED = "\033[31m"       # ERROR (40)
    BRIGHT_RED = "\033[1;31m" # CRITICAL (50)
    MAGENTA = "\033[35m"   # Custom Levels 60-80
    CYAN = "\033[36m"      # Custom Levels 90-100

# 2. Create the Custom Formatter
class PrismColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: LogColors.GRAY,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.BRIGHT_RED,
    }

    def format(self, record):
        level_num = record.levelno
        if level_num >= 90:
            color = LogColors.CYAN
        elif level_num >= 60:
            color = LogColors.MAGENTA
        else:
            color = self.LEVEL_COLORS.get(level_num, LogColors.RESET)

        formatted_message = super().format(record)
        return f"{color}{formatted_message}{LogColors.RESET}"

# 3. Configure the Handler and Formatter
handler = logging.StreamHandler()
handler.setFormatter(PrismColorFormatter(
    fmt="[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s",
    datefmt="%H:%M:%S"
))

# Apply the handler globally to the root logger (or configure per logger)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

# 4. Define your module loggers
engine_log = logging.getLogger("Engine Core")
config_log = logging.getLogger("Engine Config")
rp_thread_log = logging.getLogger("Resource Pack Thread")