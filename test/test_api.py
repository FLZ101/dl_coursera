import unittest

import requests

from dl_coursera.Crawler import Crawler
from dl_coursera.define import *

_cookies_base64_outdated = '''IyBIVFRQIENvb2tpZSBGaWxlIGRvd25sb2FkZWQgd2l0aCBjb29raWVzLnR4dCBieSBHZW51aW5vdXMgQGdlbnVpbm91cwojIFRoaXMgZmlsZSBjYW4gYmUgdXNlZCBieSB3Z2V0LCBjdXJsLCBhcmlhMmMgYW5kIG90aGVyIHN0YW5kYXJkIGNvbXBsaWFudCB0b29scy4KIyBVc2FnZSBFeGFtcGxlczoKIyAgIDEpIHdnZXQgLXggLS1sb2FkLWNvb2tpZXMgY29va2llcy50eHQgImh0dHBzOi8vd3d3LmNvdXJzZXJhLm9yZy9sZWFybi9sZWFybmluZy1ob3ctdG8tbGVhcm4iCiMgICAyKSBjdXJsIC0tY29va2llIGNvb2tpZXMudHh0ICJodHRwczovL3d3dy5jb3Vyc2VyYS5vcmcvbGVhcm4vbGVhcm5pbmctaG93LXRvLWxlYXJuIgojICAgMykgYXJpYTJjIC0tbG9hZC1jb29raWVzIGNvb2tpZXMudHh0ICJodHRwczovL3d3dy5jb3Vyc2VyYS5vcmcvbGVhcm4vbGVhcm5pbmctaG93LXRvLWxlYXJuIgojCi5jb3Vyc2VyYS5vcmcJVFJVRQkvCUZBTFNFCTE1OTU5NDY4OTMJX18yMDR1CTc5MTM3NTk0MzUtMTU2NDQxMDg5MzYwMAouY291cnNlcmEub3JnCVRSVUUJLwlGQUxTRQkxNTk4Njg1MjI3CV9fMjA0cglodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGCi5jb3Vyc2VyYS5vcmcJVFJVRQkvCUZBTFNFCTE2MzAyMzM4MjkJX2dhCUdBMS4yLjE0NjI3ODkxNTUuMTU2NzE0OTIyOQouY291cnNlcmEub3JnCVRSVUUJLwlGQUxTRQkxNTY3MjQ4MjI5CV9naWQJR0ExLjIuMTgyMDU2NTU2MS4xNTY3MTQ5MjI5Ci5jb3Vyc2VyYS5vcmcJVFJVRQkvCUZBTFNFCTE1NzQ5Mzc4MzEJX2ZicAlmYi4xLjE1NjcxNDkyMjk2ODIuMTU2OTAwNTk2MQouY291cnNlcmEub3JnCVRSVUUJLwlGQUxTRQkxNTk4Njg1Mzc3CV9oamlkCWExZWFmNWJhLWJiNWUtNGUzMi04ZjA1LTYwMWFmM2MzODYyZQouY291cnNlcmEub3JnCVRSVUUJLwlGQUxTRQkxNTY4MDEzNzk4CUNTUkYzLVRva2VuCTE1NjgwMTM3OTcuMXloNVhJWU5MWXJrTHNtZgouY291cnNlcmEub3JnCVRSVUUJLwlGQUxTRQkxNTY3MTYzNDY5CV9fNDAwdglmMDU1NWVhNS05YzkyLTRiMmQtZjVhNi1iYTIyOGViYzRkNGYKd3d3LmNvdXJzZXJhLm9yZwlGQUxTRQkvCUZBTFNFCTE1NjcxNjI3MzAJbWFJZAl7JnF1b3Q7Y2lkJnF1b3Q7OiZxdW90OzQ0YzUzYjhlYTA2MzIxNjU2YzNlNWFkODRkOTFhNTIwJnF1b3Q7LCZxdW90O3NpZCZxdW90OzomcXVvdDtiNjFhOWM3OS0wMWZhLTRiOTktYmQ2OC1mZDY2MzgyMDQ2OTUmcXVvdDt9Ci5jb3Vyc2VyYS5vcmcJVFJVRQkvCVRSVUUJMTU3MTQ4MTgyNwlDQVVUSAlGVGhWRm02SGNUeXBuSmFSRXNsbmEzcm5IaVN1MW55ZDd3VmE3eG0tSXZlOEZvWGJZVGd3eGpGS0tUVEdHUDBBTWR5RkxnN1kxMU1lVUVCcmttaTRhZy4zZVRESGpGXzU5RnRrOWRKakFmcUxBLjk3SFI1UE95UFFURDNqVmJ4eFEyaENCTGVxaFJOT3hmN3oyRVJraUFIakhqcWFWZTA1QkNFM084akVKYWhzZXdhNW1Qd2NEYmY4YTA0algyTmU0WGl4cjdoNG52RF9uMnlmUmFDYTg4MUZSTkM0WENjcjY5MWFucE5OZDNsbjVVdzVqOUYwYThiaTlxVlhqSXFvRmN2eVM5TDZSMnFfVW04NzhmeEJfbDMtaTF6enVfLXVFbkhuTGdQNDBLUlJBaAouY291cnNlcmEub3JnCVRSVUUJLwlGQUxTRQkxNTY3MTYxODg5CV9kY19ndG1fVUEtMjgzNzczNzQtMQkxCi5jb3Vyc2VyYS5vcmcJVFJVRQkvCUZBTFNFCTE1NjcxNjE4ODkJX2RjX2d0bV9VQS04NjM3MDg5MS0xCTEKd3d3LmNvdXJzZXJhLm9yZwlGQUxTRQkvCUZBTFNFCTE2MzAyMzM4MjkJX3RxX2lkLlRWLTYzNDU1NDA5LTEuMzllZAkzYjBjZTkwYTJmNjI2ZTdjLjE1NjcxNDkyMzAuMC4xNTY3MTYxODI5Li4KLmNvdXJzZXJhLm9yZwlUUlVFCS8JRkFMU0UJMTU5ODY5NzgyOQlzdGMxMTM3MTcJZW52OjE1NjcxNjE2NzAlN0MyMDE5MDkzMDEwNDExMCU3QzIwMTkwODMwMTExMzQ5JTdDMiU3QzEwMzA4ODA6MjAyMDA4MjkxMDQzNDl8dWlkOjE1NjcxNDkyMzAxMTAuMzY1MDg4NjgyLjAwODU2MDIuMTEzNzE3LjEyOTgyMDY0ODkuOjIwMjAwODI5MTA0MzQ5fHNyY2hpc3Q6MTAzMDg3OSUzQTElM0EyMDE5MDkzMDA3MTM1MCU3QzEwMzA4ODAlM0ExNTY3MTYxNjcwJTNBMjAxOTA5MzAxMDQxMTA6MjAyMDA4MjkxMDQzNDl8dHNhOjE1NjcxNjE2NzA1MzkuMTU4OTIzLjA5NTE0MDkzNC42MzA3NTYwMzQyOTEwNzUuMTg3OjIwMTkwODMwMTExMzQ5Ci5jb3Vyc2VyYS5vcmcJVFJVRQkvCUZBTFNFCTE1NjcxNjM2MzEJX180MDB2dAkxNTY3MTYxODMxMjIwCg=='''


class TestUnauthorized(unittest.TestCase):
    def test_unauthorized(self):
        with requests.Session() as sess:
            Crawler._login(sess, cookies_base64=_cookies_base64_outdated)

            course = Course(slug=COURSE_0)

            d = sess.get(URL_COURSE_1(course['slug'])).json()
            self.assertIn('elements', d)
            self.assertIn('id', d['elements'][0])

            course['id'] = d['elements'][0]['id']

            d = sess.get(URL_COURSE_2(course['slug'])).json()['linked']
            self.assertIn('onDemandCourseMaterialItems.v2', d)

            d = sess.get(URL_COURSE_REFERENCES(course['id'])).json()
            self.assertIn('errorCode', d)
            self.assertEqual(d['errorCode'], 'Not Authorized')


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sess = requests.Session()
        Crawler._login(cls.sess)

    @classmethod
    def tearDownClass(cls):
        cls.sess.close()

    def test_spec_not_exist(self):
        d = self.sess.get(URL_SPEC('SPEC-NOT-EXIST')).json()
        self.assertNotIn('elements', d)

    def test_course_not_exist(self):
        d = self.sess.get(URL_COURSE_1('COURSE-NOT-EXIST')).json()
        self.assertNotIn('elements', d)
