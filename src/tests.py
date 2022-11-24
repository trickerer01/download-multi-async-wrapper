# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from sys import exit as sysexit
from unittest import main as run_tests, TestCase

from cmdargs import parse_arglist
from defs import DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RN, DOWNLOADER_RX, BaseConfig
from executor import queues_vid, queues_img
from queries import read_queries_file, form_queries
from strings import date_str_md

args_argparse_str1 = (
    '-path ../tests '
    '-script ../tests/queries.list '
    '-fetcher ../tests '
    '-bakpath ../tests '
    '--debug '
    '--update '
    '--ignore-download-mode'
)


class ArgParseTests(TestCase):
    def test_argparse1(self) -> None:
        c = BaseConfig()
        parse_arglist(args_argparse_str1.split(), c)
        self.assertEqual(c.dest_base, '../tests/')
        self.assertEqual(c.script_path, '../tests/queries.list')
        self.assertEqual(c.fetcher_root, '../tests/')
        self.assertEqual(c.dest_bak_base, '../tests/')
        self.assertTrue(c.debug)
        self.assertTrue(c.update)
        self.assertTrue(c.ignore_download_mode)
        print('test_argparse1 passed')


class QueriesFormTests(TestCase):
    def test_queries1(self) -> None:
        c = BaseConfig()
        parse_arglist(args_argparse_str1.split(), c)
        read_queries_file(c)
        form_queries(c)
        self.assertEqual(len(queues_vid[DOWNLOADER_NM]), 1)
        self.assertEqual(len(queues_vid[DOWNLOADER_RV]), 0)
        self.assertEqual(len(queues_vid[DOWNLOADER_RN]), 0)
        self.assertEqual(len(queues_vid[DOWNLOADER_RX]), 0)
        self.assertEqual(len(queues_img[DOWNLOADER_NM]), 0)
        self.assertEqual(len(queues_img[DOWNLOADER_RV]), 0)
        self.assertEqual(len(queues_img[DOWNLOADER_RN]), 0)
        self.assertEqual(len(queues_img[DOWNLOADER_RX]), 2)
        self.assertEqual(
            queues_vid[DOWNLOADER_NM][0],
            f'python3 D:/nm/ids.py -start 1 -end 1 -path "../tests/{date_str_md(False)}/" --dump-tags --verbose -script "'
            'a: -quality 1080p -a -b -c -dfff ggg; '
            'b: -quality 1080p -a -b -c -dfff -ggg -(x,z) (h~i~j~k); '
            'c: -quality 1080p -a -b -c -dfff -ggg -h -i -j -k (l~m~n); '
            'd: -quality 1080p -a -b -c -ggg -h -i -j -k -l -m -n -quality 360p -uvp always"'
        )
        self.assertEqual(
            queues_img[DOWNLOADER_RX][0],
            f'python3 D:/ruxx/app_gui.py id:>=1 id:<=1 -path "../tests/{date_str_md(True)}/a/" -module rx a'
        )
        self.assertEqual(
            queues_img[DOWNLOADER_RX][1],
            f'python3 D:/ruxx/app_gui.py id:>=1 id:<=1 -path "../tests/{date_str_md(True)}/b/" -module rx -a b'
        )
        print('test_queries1 passed')


def run_all_tests() -> None:
    res = run_tests(module='tests', exit=False)
    if not res.result.wasSuccessful():
        print('Fail')
        sysexit()


if __name__ == '__main__':
    run_all_tests()

#
#
#########################################
