from enum import Enum

import requests
from docker import ContextAPI


class Status(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELED = "canceled"


class MetricsSource:
    CLI = "docker-compose"


METRICS_PORT = 9000


class MetricsCommand:
    """
    Representation of a command in the metrics.
    """

    def __init__(self, command,
                 context_type=None,
                 status=Status.SUCCESS,
                 source=MetricsSource.CLI,
                 url="http://localhost:" + str(METRICS_PORT) + "/usage"):
        self.command = "compose " + command if command else "compose --help"
        self.context = context_type or ContextAPI.get_current_context().context_type or 'moby'
        self.source = source
        self.status = status.value
        self.url = url

    def send(self):
        try:
            return requests.post(self.url, json=self.to_map(), timeout=.05)
        except Exception as e:
            return e

    def to_map(self):
        return {
            'command': self.command,
            'context': self.context,
            'source': self.source,
            'status': self.status,
        }
