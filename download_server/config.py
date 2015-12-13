import os

ROOT_DIR = os.path.dirname(__file__)

TORNADO_APP_SETTINGS = {'debug': True}
TORNADO_PORT = 8000
TORNADO_ADDR = 'localhost'
PUBLIC_FILE_DIR = os.path.join(ROOT_DIR, 'public')

ARIA2_RPC_ADDRESS = 'http://localhost:6800/rpc'
