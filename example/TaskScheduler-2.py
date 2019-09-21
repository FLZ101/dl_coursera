import time
import random
import threading

from dl_coursera.lib.TaskScheduler import TaskScheduler

ts = TaskScheduler()


@ts.register_task
def f(*, s):
    d = ts.d

    if d.get('xxx') is None:
        d['xxx'] = [s] * 3

    for _ in d['xxx']:
        time.sleep(random.uniform(0.5, 1.5))
        print(threading.current_thread().name, '-', _)


def main():
    ts.start(n_worker=3)

    for s in ['Alice', 'Bob', 'Cindy', 'Dave']:
        f(s=s)

    ts.wait()


if __name__ == '__main__':
    main()
