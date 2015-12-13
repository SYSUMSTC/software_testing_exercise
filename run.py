#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import atexit
import os.path
import signal
import sys
import uuid
from subprocess import Popen

import tornado.ioloop

from download_server import config, web_service


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', help='the address to bind',
                        default=config.TORNADO_ADDR)
    parser.add_argument('--port', help='the port to bind', type=int,
                        default=config.TORNADO_PORT)
    parser.add_argument('--run', help='the directory to store running data',
                        default=config.ROOT_DIR)
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    session_file = os.path.join(args.run, '.aria2_session')
    download_file_dir = os.path.join(args.run, 'download')

    # generate a UUID as the aria2 RPC token
    aria2_token = uuid.uuid4().hex
    aria2_args = ['aria2c',
                  '--enable-rpc',
                  '--rpc-secret', aria2_token,
                  '--save-session', session_file]
    if os.path.exists(session_file):
        aria2_args.extend(['--input-file', session_file])
    aria2_proc = Popen(' '.join(aria2_args), shell=True)

    @atexit.register
    def kill_aria2():
        aria2_proc.terminate()
        aria2_proc.wait()
    signal.signal(signal.SIGTERM, lambda *a: sys.exit())

    app = web_service.create_app(aria2_token, download_file_dir)
    app.listen(config.TORNADO_PORT, config.TORNADO_ADDR)
    tornado.ioloop.IOLoop.current().start()
