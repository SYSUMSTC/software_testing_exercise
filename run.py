#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import atexit
import os.path
import signal
import sys
import uuid
from subprocess import Popen

import tornado.ioloop

from download_server import config, web_service

if __name__ == "__main__":
    # generate a UUID as the aria2 RPC token
    aria2_token = uuid.uuid4().hex
    aria2_args = ['aria2c',
                  '--enable-rpc',
                  '--rpc-secret', aria2_token,
                  '--save-session', config.ARIA2_SESSION_FILE]
    if os.path.exists(config.ARIA2_SESSION_FILE):
        aria2_args.extend(['--input-file', config.ARIA2_SESSION_FILE])
    aria2_proc = Popen(' '.join(aria2_args), shell=True)

    @atexit.register
    def kill_aria2():
        aria2_proc.terminate()
        aria2_proc.wait()
    signal.signal(signal.SIGTERM, lambda *a: sys.exit())

    app = web_service.create_app(aria2_token)
    app.listen(config.TORNADO_PORT, config.TORNADO_ADDR)
    tornado.ioloop.IOLoop.current().start()
