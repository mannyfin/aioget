# import os
from pathlib import Path

PROJ_ROOT = Path(__file__).parent.parent.parent.__str__()  # os.path.abspath(os.path.join("..", os.pardir))
CONFIG_DIR = Path(__file__).parent.parent.__str__()  # os.path.abspath(os.path.join(PROJ_ROOT, 'configs'))
ASYNC_SLEEP = 0.01
INITIAL_SLEEP = 10

