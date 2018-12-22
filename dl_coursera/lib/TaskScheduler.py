import math
import queue
import threading
import traceback
import logging
import functools
import re

from .misc import format_dict


class Task:
    LOWEST_PRIO = ''
    HIGHEST_PRIO = 'ZZZZZZZ'

    _re_priority = re.compile(r'^[A-Z]{1,6}$')

    class ShouldNotRun(Exception):
        pass

    def __init__(self, *, priority, ttl, _isSpecial=False):
        """
        @priority: should be a string that matches the following Python regular expression: `[A-Z]{1, 6}`
        @ttl: maximum times to try
        """

        self._priority = priority
        self._ttl = ttl

        if not _isSpecial:
            assert Task._re_priority.match(self._priority) is not None

    def __lt__(self, other):
        return self._priority > other._priority

    def should_run(self):
        return self._ttl > 0

    def run(self):
        if not self.should_run():
            raise Task.ShouldNotRun(self)
        else:
            self._ttl -= 1
            self.go()

    def go():
        pass


_shutdown_task = Task(priority=Task.HIGHEST_PRIO, ttl=1, _isSpecial=True)


class FuncTask(Task):
    def __init__(self, *, priority='A', ttl=1, func, kwargs=None, format_kwargs=None, desc=None):
        super().__init__(priority=priority, ttl=ttl)

        self._func = func
        self._kwargs = {} if kwargs is None else kwargs

        self._desc = 'priority=%s, ttl=%s' % (priority, ttl)
        self._desc = '%s. %s' % (self._desc, desc or func.__name__)

        _s = (format_kwargs or format_dict)(kwargs)
        if len(_s) > 0:
            self._desc = '%s: %s' % (self._desc, _s)

    @property
    def kwargs(self):
        return self._kwargs

    def __str__(self):
        return self._desc

    def go(self):
        self._func(**self._kwargs)


class TaskScheduler:
    def __init__(self):
        self._init()

    def _init(self):
        self._q = queue.PriorityQueue()
        self._threads = []

        self._n_worker = 0
        self._n_worker_lock = threading.Lock()

        self._shutdown_event = threading.Event()

        self._failures = []
        self._failures_lock = threading.Lock()

        self._threading_local = threading.local()
        self._threading_local.task = None

    def add_task(self, task):
        self._q.put(task)

    def wait(self):
        self._q.join()

        with self._failures_lock:
            res, self._failures[:] = self._failures[:], []
        return res

    def shutdown(self):
        assert len(self._threads) == self._n_worker

        if len(self._threads) == 0:
            return

        for _ in range(len(self._threads)):
            self.add_task(_shutdown_task)

        self._shutdown_event.wait()

        for _ in self._threads:
            _.join()

        self._init()

    def _onshutdown(self):
        with self._n_worker_lock:
            self._n_worker -= 1

            if self._n_worker == 0:
                self._shutdown_event.set()

    def start(self, *, n_worker=3, WorkerFactory=threading.Thread):
        n = math.floor(math.log10(n_worker)) + 1
        for i in range(1, n_worker + 1):
            t = WorkerFactory(target=self._func_work, daemon=True, name='%%0%dd' % n % i)
            t.start()
            self._threads.append(t)

        self._n_worker = n_worker

    def register_task(self, func=None, *, FuncTaskFactory=FuncTask, **_kwargs):
        if func is None:
            return functools.partial(self.register_task, FuncTaskFactory=FuncTaskFactory, **_kwargs)

        @functools.wraps(func)
        def _func(**kwargs):
            self.add_task(FuncTaskFactory(func=func, kwargs=kwargs, **_kwargs))

        return _func

    def _add_failure(self, _failure):
        with self._failures_lock:
            self._failures.append(_failure)

    def _func_work(self):
        logging.debug('started')

        while True:
            task = self._q.get()
            self._threading_local.task = task

            if task is _shutdown_task:
                self._onshutdown()
                logging.debug('shutdowned')
                break

            try:
                logging.info('[Doing] %s' % task)
                task.run()
            except Exception:
                tb_msg = traceback.format_exc()
                if task.should_run():
                    self.add_task(task)
                    logging.warning('[Retry later] %s\n%s' % (task, tb_msg))
                else:
                    self._add_failure((task, tb_msg))
                    logging.error('[Failed] %s\n%s' % (task, tb_msg))
            else:
                logging.info('[Done] %s' % task)

            self._q.task_done()

    def current_task(self):
        return self._threading_local.task

    @property
    def d(self):
        try:
            self._threading_local.d
        except AttributeError:
            self._threading_local.d = {}

        return self._threading_local.d

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()
