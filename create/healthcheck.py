"""Check the status of this create worker.

This runs the "status" task on a celery queue with the name of this hostname.
http://docs.celeryproject.org/en/latest/userguide/routing.html#manual-routing

If the healthcheck fails, Marathon will bring up additional instances and
retire this one.
"""
import configparser
import socket
import ssl

from celery import Celery
from ocflib.account import submission


def celery_app():
    # TODO: reduce duplication with create.tasks
    conf = configparser.ConfigParser()
    conf.read('/etc/ocf-create/ocf-create.conf')

    celery = Celery(
        broker=conf.get('celery', 'broker'),
        backend=conf.get('celery', 'backend'),
    )
    # TODO: use ssl verification
    celery.conf.broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE,
    }
    # `redis_backend_use_ssl` is an OCF patch which was proposed upstream:
    # https://github.com/celery/celery/pull/3831
    celery.conf.redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE,
    }

    # TODO: stop using pickle
    celery.conf.task_serializer = 'pickle'
    celery.conf.result_serializer = 'pickle'
    celery.conf.accept_content = {'pickle'}

    return celery


def main():
    tasks = submission.get_tasks(celery_app())
    task = tasks.status.apply_async(queue=socket.gethostname(), args=())
    result = task.wait(timeout=5)
    print(result)


if __name__ == '__main__':
    exit(main())
