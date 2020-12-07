import logging
import sys
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Thread

import requests

from ..acceptance.cli_test import dispatch
from compose.metrics.client import METRICS_PORT
from tests.integration.testcases import DockerClientTestCase


class MetricsTest(DockerClientTestCase):
    base_dir = 'tests/fixtures/v3-full'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        MetricsServer().start()

    @classmethod
    def test_metrics_help(cls):
        dispatch(cls.base_dir, [])  # root `docker-compose` command is considered as a `--help`
        assert cls.get_content() == \
               b'{"command": "compose --help", "context": "moby", ' \
               b'"source": "docker-compose", "status": "success"}'
        dispatch(cls.base_dir, ['help', 'run'])
        assert cls.get_content() == \
               b'{"command": "compose help", "context": "moby", ' \
               b'"source": "docker-compose", "status": "success"}'
        dispatch(cls.base_dir, ['--help'])
        assert cls.get_content() == \
               b'{"command": "compose --help", "context": "moby", ' \
               b'"source": "docker-compose", "status": "success"}'
        dispatch(cls.base_dir, ['run', '--help'])
        assert cls.get_content() == \
               b'{"command": "compose --help run", "context": "moby", ' \
               b'"source": "docker-compose", "status": "success"}'
        dispatch(cls.base_dir, ['up', '--help', 'extra_args'])
        assert cls.get_content() == \
               b'{"command": "compose --help up", "context": "moby", ' \
               b'"source": "docker-compose", "status": "success"}'

    @classmethod
    def test_metrics_simple_commands(cls):
        dispatch(cls.base_dir, ['ps'])
        assert cls.get_content() == \
               b'{"command": "compose ps", "context": "moby", ' \
               b'"source": "docker-compose", "status": "success"}'
        dispatch(cls.base_dir, ['version'])
        assert cls.get_content() == \
               b'{"command": "compose version", "context": "moby", ' \
               b'"source": "docker-compose", "status": "success"}'
        dispatch(cls.base_dir, ['version', '--yyy'])
        assert cls.get_content() == \
               b'{"command": "compose version", "context": "moby", ' \
               b'"source": "docker-compose", "status": "failure"}'

    @staticmethod
    def get_content():
        resp = requests.get('http://localhost:' + str(METRICS_PORT) + '/usage')
        print(resp.content)
        return resp.content


def start_server(url, port):
    httpd = HTTPServer((url, port), MetricsHTTPRequestHandler)
    httpd.serve_forever()


class MetricsServer:
    def __init__(self, url='localhost', port=METRICS_PORT):
        self.url = url
        self.port = port

    def start(self):
        t = Thread(target=start_server, args=(self.url, self.port), daemon=True)
        t.start()


class MetricsHTTPRequestHandler(BaseHTTPRequestHandler):
    usages = []

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        for u in MetricsHTTPRequestHandler.usages:
            self.wfile.write(u)
        MetricsHTTPRequestHandler.usages = []

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        MetricsHTTPRequestHandler.usages.append(body)
        self.send_response(200)
        self.end_headers()


if __name__ == '__main__':
    logging.getLogger("urllib3").propagate = False
    logging.getLogger("requests").propagate = False
    start_server(sys.argv[1], int(sys.argv[2]))
