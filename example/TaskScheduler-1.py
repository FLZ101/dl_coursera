import time

from dl_coursera.lib.TaskScheduler import TaskScheduler

ts = TaskScheduler()


@ts.register_task
def f(*, n):
    time.sleep(1)
    print('f', n)

    g(n=n + 1)
    g(n=n + 1)


@ts.register_task
def g(*, n):
    time.sleep(1)
    print('g', n)

    h(n=n + 1)
    h(n=n + 1)


@ts.register_task
def h(*, n):
    time.sleep(1)
    print('h', n)


if __name__ == '__main__':
    ts.start(n_worker=10)
    f(n=1)
    ts.wait()
