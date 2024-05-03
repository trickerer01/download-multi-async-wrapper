# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from unittest import TestCase

from cmdargs import parse_arglist
from defs import Config, DOWNLOADER_NM, DOWNLOADER_RV, DOWNLOADER_RC, DOWNLOADER_RN, DOWNLOADER_RX, DOWNLOADER_RS
from executor import queries_all
from main import main_sync
from queries import read_queries_file, prepare_queries
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


def set_up_test(log=False) -> None:
    # noinspection PyProtectedMember
    Config._reset()
    Config.test = True
    Config.console_log = log


class ArgParseTests(TestCase):
    def test_argparse1(self) -> None:
        set_up_test()
        parse_arglist(args_argparse_str1.split())
        self.assertEqual(
            'debug: False, downloaders: [\'nm\', \'rv\', \'rc\', \'rn\', \'rx\', \'rs\'], script: ../tests/queries.list, dest: ./, '
            'run: ./, logs: ./, bak: ./, update: False, no_download: False, ignore_download_mode: False, '
            'max_cmd_len: 16000',
            str(Config)
        )
        print(f'{self._testMethodName} passed')

    def test_argparse2(self) -> None:
        set_up_test()
        parse_arglist(args_argparse_str2.split())
        self.assertEqual(
            'debug: True, downloaders: [\'rv\', \'rn\', \'rx\', \'rs\'], script: ../tests/queries.list, dest: ../tests/, '
            'run: ../run/, logs: ../logs/, bak: ../bak/, update: True, no_download: False, ignore_download_mode: True, '
            'max_cmd_len: 16000',
            str(Config)
        )
        print(f'{self._testMethodName} passed')


class QueriesFormTests(TestCase):
    def test_queries1(self) -> None:
        set_up_test()
        parse_arglist(args_argparse_str2.split())
        read_queries_file()
        prepare_queries()
        self.assertEqual('python3', Config.python)
        self.assertEqual(1, len(queries_all['VID'][DOWNLOADER_NM]))
        self.assertEqual(3, len(queries_all['VID'][DOWNLOADER_RV]))
        self.assertEqual(0, len(queries_all['VID'][DOWNLOADER_RC]))
        self.assertEqual(0, len(queries_all['VID'][DOWNLOADER_RN]))
        self.assertEqual(0, len(queries_all['VID'][DOWNLOADER_RX]))
        self.assertEqual(0, len(queries_all['VID'][DOWNLOADER_RS]))
        self.assertEqual(0, len(queries_all['IMA'][DOWNLOADER_NM]))
        self.assertEqual(0, len(queries_all['IMA'][DOWNLOADER_RV]))
        self.assertEqual(0, len(queries_all['IMA'][DOWNLOADER_RC]))
        self.assertEqual(0, len(queries_all['IMA'][DOWNLOADER_RN]))
        self.assertEqual(2, len(queries_all['IMA'][DOWNLOADER_RX]))
        self.assertEqual(0, len(queries_all['IMA'][DOWNLOADER_RS]))
        self.assertEqual(
            f'python3 "D:/NM/src/ids.py" -start 1 -end 1 -path "../tests/{date_str_md("VID")}/" --dump-tags -script "'
            'a: -quality 1080p -a -b -c -dfff ggg; '
            'b: -quality 1080p -a -b -c -dfff -ggg -(x,z) (h~i~j~k); '
            'c: -quality 1080p -a -b -c -dfff -ggg -h -i -j -k (l~m~n); '
            'd: -a -b -c -ggg -h -i -j -k -l -m -n -quality 360p -uvp always"',
            queries_all['VID'][DOWNLOADER_NM][0]
        )
        self.assertEqual(
            f'python3 "D:/old/RV/src/pages.py" -pages 5 -start 2 -stop_id 5 -begin_id 9 -path "../tests/{date_str_md("VID")}/a/" '
            '-log info -timeout 15 -retries 50 -throttle 30 --dump-descriptions --dump-tags --dump-comments '
            '-quality 1080p -search a',
            queries_all['VID'][DOWNLOADER_RV][0]
        )
        self.assertEqual(
            f'python3 "D:/old/RV/src/pages.py" -pages 5 -start 2 -stop_id 5 -begin_id 9 -path "../tests/{date_str_md("VID")}/b/" '
            '-log info -timeout 15 -retries 50 -throttle 30 --dump-descriptions --dump-tags --dump-comments '
            '-quality 1080p -search_tag b,c,d -search_rule_tag any',
            queries_all['VID'][DOWNLOADER_RV][1]
        )
        self.assertEqual(
            f'python3 "D:/old/RV/src/pages.py" -pages 5 -start 2 -stop_id 5 -begin_id 9 -path "../tests/{date_str_md("VID")}/c/" '
            '-log info -timeout 15 -retries 50 -throttle 30 --dump-descriptions --dump-tags --dump-comments '
            '-quality 1080p -b -c -d -(g,h,i) -search_tag e,f -search_rule_tag all',
            queries_all['VID'][DOWNLOADER_RV][2]
        )
        self.assertEqual(
            f'python3 "D:/ruxx/src/ruxx_cmd.py" id:>=1 id:<=1 -path "../tests/{date_str_md("IMA")}/a/" -module rx a',
            queries_all['IMA'][DOWNLOADER_RX][0]
        )
        self.assertEqual(
            f'python3 "D:/ruxx/src/ruxx_cmd.py" id:>=1 id:<=1 -path "../tests/{date_str_md("IMA")}/b/" -module rx -a b (+c+~+d+)',
            queries_all['IMA'][DOWNLOADER_RX][1]
        )
        print(f'{self._testMethodName} passed')


class RunTests(TestCase):
    def test_main1(self) -> None:
        set_up_test()
        main_sync(('-script', '"../tests/queries.list"', '-logspath', '../logs/archive',
                   '--debug', '--no-download', '-downloaders', 'rx,nm,rn,rs'))
        print(f'{self._testMethodName} passed')

    def test_main2(self) -> None:
        set_up_test()
        main_sync(('-script', '"../tests/queries.list"', '-logspath', '../logs/archive',
                   '--debug', '-downloaders', 'rx,nm,rn,rs'))
        print(f'{self._testMethodName} passed')

    def test_main3(self) -> None:
        set_up_test()
        main_sync(('-script', '"../tests/queries.list"', '-logspath', '../logs/archive',
                   '-downloaders', 'rx,nm,rn,rs'))
        print(f'{self._testMethodName} passed')

#
#
#########################################
