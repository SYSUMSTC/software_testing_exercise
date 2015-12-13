import itertools
import json
import os.path
import xmlrpc.client

import tornado.web

from . import config

TASK_FIELDS = ['gid', 'status', 'totalLength', 'completedLength',
               'downloadSpeed', 'errorMessage', 'files', 'dir']


class TaskHandler(tornado.web.RequestHandler):
    """RequestHandler for download task management.

    The APIs provided are actually wrappers for the underlying aria2.
    For more details about aria2's RPCs, see
    http://aria2.sourceforge.net/manual/en/html/aria2c.html#rpc-interface"""

    def initialize(self, rpc, token):
        self._rpc = rpc
        self._token = 'token:' + token

    def get(self):
        """Gets tasks details.

        - GET /task
        Returns a dict with a 'tasks' field containing the details of all
        tasks.

        - GET /task?gid=XXXXXX
        Returns the details of task XXXXXX.
        """
        gid = self.get_query_argument('gid', None)

        if gid:  # get a specified task
            self.write(update_fields(
                self._rpc.aria2.tellStatus(self._token, gid, TASK_FIELDS)))

        else:  # get all tasks
            active_tasks = self._rpc.aria2.tellActive(self._token, TASK_FIELDS)
            waiting_tasks = self._rpc.aria2.tellWaiting(
                self._token, -1, 100, TASK_FIELDS)
            stopped_tasks = self._rpc.aria2.tellStopped(
                self._token, -1, 100, TASK_FIELDS)
            all_tasks = [
                update_fields(task) for task in
                itertools.chain(active_tasks, waiting_tasks, stopped_tasks)
            ]
            self.write({'tasks': all_tasks})

    def post(self):
        """Applies and action on a given task or create a task.

        - POST /task {"gid": "XXXXXX", "action": "ACTION"}
        Applies action ACTION on task XXXXXX. Supported actions are 'pause' and
        'resume'.

        - POST /task {"url": "http://some.file.to/download"}
        Creates a task to download http://some.file.to/download.

        Returns the gid of the task on success.
        """
        params = json.loads(self.request.body.decode())
        gid = params.get('gid')

        if gid:  # apply an action on a specified task
            action = params.get('action')
            if action == 'pause':
                self.write(self._rpc.aria2.pause(self._token, gid))
            elif action == 'resume':
                self.write(self._rpc.aria2.unpause(self._token, gid))
            else:  # invalid action
                self.send_error(400)

        else:  # create a task
            url = params.get('url')
            self.write(self._rpc.aria2.addUri(
                self._token, [url], {'dir': config.DOWNLOAD_FILE_DIR}))

    def delete(self):
        """Stops a given task.

        - DELETE /task?gid=XXXXXX
        Stops the task XXXXXX. Returns the task gid on success.
        """
        # gid must be specified for deletion
        gid = self.get_query_argument('gid')
        self.write(self._rpc.aria2.remove(self._token, gid))


def update_fields(task):
    """Updates some fields of the task object returned by aria2 RPC.

    Fields 'totalLength', 'completedLength' and 'downloadSpeed' are cast to
    integers, fields 'files' and 'dir' are converted to 'filename'.
    """
    task['totalLength'] = int(task['totalLength'])
    task['completedLength'] = int(task['completedLength'])
    task['downloadSpeed'] = int(task['downloadSpeed'])
    task['eta'] = calculate_eta(task)

    if task['files']:
        # there might be multiple files for BT tasks, but we don't support BT
        path = task['files'][0]['path']
        if path:
            filename = os.path.relpath(path, task['dir'])
            task['filename'] = filename
            # the following fields are not needed and should not be exposed
            task.pop('files')
            task.pop('dir')

    return task


def calculate_eta(task):
    """Estimates the remaining time required to finish a task."""
    if task['status'] == 'active':
        if task['downloadSpeed'] == 0:
            return None  # NaN is not part of JSON
        else:
            return ((task['totalLength'] - task['completedLength'])
                    / task['downloadSpeed'])
    elif task['status'] == 'complete':
        return 0.0
    else:
        return None


def create_downloader_rpc_stub(address=None):
    """Creates a XML-RPC stub object connected to aria2.

    We are using xmlrpc.client here, but it uses blocking IO, which is normally
    wrong when using within a tornado app, which is single-threaded
    asynchronous. But as aria2 is running locally and we are just making a toy
    demo for exercise, we can just ignore there issues.
    """
    return xmlrpc.client.ServerProxy(address or config.ARIA2_RPC_ADDRESS,
                                     allow_none=True)


def create_app(aria2_token, rpc=None):
    """Creates a tornado application."""
    rpc = rpc or create_downloader_rpc_stub()
    return tornado.web.Application([
        ('/task', TaskHandler, {'rpc': rpc, 'token': aria2_token}),
        ('/download/(.*)', tornado.web.StaticFileHandler,
         {'path': config.DOWNLOAD_FILE_DIR}),
        ('/(.*)', tornado.web.StaticFileHandler,
         {'path': config.PUBLIC_FILE_DIR, 'default_filename': 'index.html'}),
    ], **config.TORNADO_APP_SETTINGS)
