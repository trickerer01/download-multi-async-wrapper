# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from unittest import TestCase

from cmdargs import parse_arglist
from defs import DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RN, DOWNLOADER_RX, DOWNLOADER_RS, BaseConfig
from executor import ques_vid, ques_img
from main import main_sync
from queries import read_queries_file, form_queries
from strings import date_str_md

__all__ = ()

args_argparse_str1 = (
    '-script ../tests/queries.list'
)

args_argparse_str2 = (
    '--debug '
    '-downloaders rv,rx,rn,rs '
    '-path ../tests '
    '-script "../tests/queries.list" '
    '--ignore-download-mode '
    '--update '
    '-runpath ../run '
    '-logspath ../logs '
    '-bakpath ../bak'
)


class ArgParseTests(TestCase):
    def test_argparse1(self) -> None:
        c = BaseConfig(test=True)
        parse_arglist(args_argparse_str1.split(), c)
        self.assertEqual(
            'debug: False, downloaders: [\'nm\', \'rv\', \'rn\', \'rx\', \'rs\'], script: ../tests/queries.list, dest: ./, '
            'run: ./, logs: ./, bak: ./, update: False, no_download: False, ignore_download_mode: False, '
            'max_cmd_len: 16000',
            str(c)
        )
        print(f'{self._testMethodName} passed')

    def test_argparse2(self) -> None:
        c = BaseConfig(test=True)
        parse_arglist(args_argparse_str2.split(), c)
        self.assertEqual(
            str(c),
            'debug: True, downloaders: [\'rv\', \'rn\', \'rx\', \'rs\'], script: ../tests/queries.list, dest: ../tests/, '
            'run: ../run/, logs: ../logs/, bak: ../bak/, update: True, no_download: False, ignore_download_mode: True, '
            'max_cmd_len: 16000'
        )
        print(f'{self._testMethodName} passed')


class QueriesFormTests(TestCase):
    def test_queries1(self) -> None:
        c = BaseConfig(test=True)
        parse_arglist(args_argparse_str2.split(), c)
        read_queries_file(c)
        form_queries(c)
        self.assertEqual('python3', c.python)
        self.assertEqual(1, len(ques_vid[DOWNLOADER_NM]))
        self.assertEqual(0, len(ques_vid[DOWNLOADER_RV]))
        self.assertEqual(0, len(ques_vid[DOWNLOADER_RN]))
        self.assertEqual(0, len(ques_vid[DOWNLOADER_RX]))
        self.assertEqual(0, len(ques_vid[DOWNLOADER_RS]))
        self.assertEqual(0, len(ques_img[DOWNLOADER_NM]))
        self.assertEqual(0, len(ques_img[DOWNLOADER_RV]))
        self.assertEqual(0, len(ques_img[DOWNLOADER_RN]))
        self.assertEqual(2, len(ques_img[DOWNLOADER_RX]))
        self.assertEqual(0, len(ques_img[DOWNLOADER_RS]))
        self.assertEqual(
            ques_vid[DOWNLOADER_NM][0],
            f'python3 "D:/nm/src/ids.py" -start 1 -end 1 -path "../tests/{date_str_md(False)}/" --dump-tags --verbose -script "'
            'a: -quality 1080p -a -b -c -dfff ggg; '
            'b: -quality 1080p -a -b -c -dfff -ggg -(x,z) (h~i~j~k); '
            'c: -quality 1080p -a -b -c -dfff -ggg -h -i -j -k (l~m~n); '
            'd: -a -b -c -ggg -h -i -j -k -l -m -n -quality 360p -uvp always"'
        )
        self.assertEqual(
            ques_img[DOWNLOADER_RX][0],
            f'python3 "D:/ruxx/src/ruxx.py" id:>=1 id:<=1 -path "../tests/{date_str_md(True)}/a/" -module rx a'
        )
        self.assertEqual(
            ques_img[DOWNLOADER_RX][1],
            f'python3 "D:/ruxx/src/ruxx.py" id:>=1 id:<=1 -path "../tests/{date_str_md(True)}/b/" -module rx -a b (+c+~+d+)'
        )
        print(f'{self._testMethodName} passed')


class RunTests(TestCase):
    def test_main1(self) -> None:
        c = BaseConfig(test=True)
        main_sync(('-script', '"../tests/queries.list"', '-logspath', '../logs/archive',
                   '--debug', '--no-download', '-downloaders', 'rx,nm,rn,rs'), c)
        print(f'{self._testMethodName} passed')

    def test_main2(self) -> None:
        c = BaseConfig(test=True)
        main_sync(('-script', '"../tests/queries.list"', '-logspath', '../logs/archive',
                   '--debug', '-downloaders', 'rx,nm,rn,rs'), c)
        print(f'{self._testMethodName} passed')

    def test_main3(self) -> None:
        c = BaseConfig(test=True)
        main_sync(('-script', '"../tests/queries.list"', '-logspath', '../logs/archive',
                   '-downloaders', 'rx,nm,rn,rs'), c)
        print(f'{self._testMethodName} passed')

#
#
#########################################
