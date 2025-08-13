import os
import logging
import random

import requests

from dl_coursera.lib.TaskScheduler import TaskScheduler
from dl_coursera.Crawler import Crawler


def test_crawler():
    with TaskScheduler() as ts, requests.Session() as sess:
        ts.start(n_worker=1)
        crawler = Crawler(ts=ts, sess=sess)
        crawler.login()

        _ = [
            '20cnwm',
            'advanced-modeling',
            'algorithms-part1',
            'complex-analysis',
            'crypto',
            'game-theory-1',
            'genetic-lab',
            'happiness',
            'learning-how-to-learn',
            'lisan-youhua-jianmo-jichupian',
            'ma-ke-si',
            'machine-design1',
            'machine-learning',
            'mathematical-thinking',
            'modern-postmodern-1',
            'networks-illustrated',
            'renqun-wangluo',
            'shengwu-yanhua',
            'understanding-arguments',
            'yoga',
        ]
        crawler.crawl(slug=random.choice(_), isSpec=False)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(threadName)s - %(message)s'
    )
    test_crawler()
