# coding: utf-8
# Copyright 2013 The Font Bakery Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See AUTHORS.txt for the list of Authors and LICENSE.txt for the License.

import logging

import gevent
from flask import Response, current_app
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from flask.ext.rq import get_connection
from rq import Worker

from flask import (Blueprint, request)

realtime = Blueprint('realtime', __name__)


class BuildNamespace(BaseNamespace, BroadcastMixin):

    def __init__(self, *args, **kwargs):
        r = kwargs.get('request', None)
        if hasattr(r, '_conn'):
            self._conn = r._conn
        super(BuildNamespace, self).__init__(*args, **kwargs)

    # def initialize(self):
    #     print("Socketio session started")

    # def on_start(self):
    #     self.emit('start', {})

    # def on_stop(self):
    #     self.emit('stop', {})

    # def on_hello(self, message):
    #     print(message)
    #     self.emit('ping', {})

    # def recv_message(self, message):
    #     print ("PING!!!", message)

    def recv_connect(self):
        def check_queue():
            while True:
                if any([w.state != 'idle' for w in Worker.all(self._conn)]):
                    self.emit('start', {})
                else:
                    self.emit('stop', {})
                gevent.sleep(0.3)
        self.spawn(check_queue)

@realtime.route('/socket.io/<path:remaining>')
def socketio(remaining):
    real_request = request._get_current_object()
    real_request._conn = get_connection()
    socketio_manage(request.environ, {
        '/build': BuildNamespace,
        }, request=real_request)
    return Response()