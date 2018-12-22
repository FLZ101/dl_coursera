import time
import logging

from dl_coursera.lib.TaskScheduler import TaskScheduler

ts = TaskScheduler()


@ts.register_task
def f(*, i, s):
    time.sleep(i)
    logging.info(s)


def main():
    def _run():
        for i, s in enumerate(['Alice', 'Bob', 'Jodie', 'He', 'Cindy']):
            f(i=i, s=s)

    ts.start(n_worker=3)
    _run()
    time.sleep(3)
    ts.shutdown()

    with ts:
        ts.start(n_worker=3)
        _run()
        ts.wait()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(asctime)s - %(threadName)s - %(message)s')
    main()
