import time


def f(n):
    time.sleep(1)
    print('f', n)

    g(n + 1)
    g(n + 1)


def g(n):
    time.sleep(1)
    print('g', n)

    h(n + 1)
    h(n + 1)


def h(n):
    time.sleep(1)
    print('h', n)


if __name__ == '__main__':
    f(1)
