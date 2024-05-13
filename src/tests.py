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
# noinspection PyProtectedMember
from queries import (
    read_queries_file, prepare_queries, sequences_ids, sequences_pages, sequences_paths, sequences_common, sequences_tags,
    sequences_subfolders
)
from strings import date_str_md

__all__ = ()

args_argparse_str1 = (
    '-script ../tests/queries.list'
)

args_argparse_str2 = (
    '--debug '
    '--ignore-download-mode '
    '-downloaders rv,rx,rn,rs '
    '-path ../tests '
    '-script "../tests/queries.list"'
)

args_argparse_str3 = (
    '-script ../tests/queries2.list'
)

args_argparse_str4 = (
    args_argparse_str3 + ' -path C:/'
)


def set_up_test(log=False) -> None:
    # noinspection PyProtectedMember
    Config._reset()
    Config.test = True
    Config.console_log = log
    sequences_ids.clear()
    sequences_pages.clear()
    sequences_paths.clear()
    sequences_common.clear()
    sequences_tags.clear()
    sequences_subfolders.clear()


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
            'run: ./, logs: ./, bak: ./, update: False, no_download: False, ignore_download_mode: True, '
            'max_cmd_len: 16000',
            str(Config)
        )
        print(f'{self._testMethodName} passed')


class QueriesFormTests(TestCase):
    def test_queries1(self) -> None:
        cat_vid, cat_img, cat_vid_ = 'VIDEOS', 'IMAGES', 'VIDEOS '
        set_up_test()
        parse_arglist(args_argparse_str2.split())
        read_queries_file()
        prepare_queries()
        self.assertEqual('script_0', Config.title)
        self.assertTrue(Config.datesub)
        self.assertTrue(Config.lookahead)
        self.assertTrue(Config.update)
        self.assertEqual('../bak/', Config.dest_bak_base)
        self.assertEqual('../run/', Config.dest_run_base)
        self.assertEqual('../logs/', Config.dest_logs_base)
        self.assertEqual('python3', Config.python)
        self.assertEqual(1, len(queries_all[cat_vid][DOWNLOADER_NM]))
        self.assertEqual(3, len(queries_all[cat_vid][DOWNLOADER_RV]))
        self.assertEqual(0, len(queries_all[cat_vid][DOWNLOADER_RC]))
        self.assertEqual(0, len(queries_all[cat_vid][DOWNLOADER_RN]))
        self.assertEqual(0, len(queries_all[cat_vid][DOWNLOADER_RX]))
        self.assertEqual(0, len(queries_all[cat_vid][DOWNLOADER_RS]))
        self.assertEqual(0, len(queries_all[cat_img][DOWNLOADER_NM]))
        self.assertEqual(0, len(queries_all[cat_img][DOWNLOADER_RV]))
        self.assertEqual(0, len(queries_all[cat_img][DOWNLOADER_RC]))
        self.assertEqual(0, len(queries_all[cat_img][DOWNLOADER_RN]))
        self.assertEqual(2, len(queries_all[cat_img][DOWNLOADER_RX]))
        self.assertEqual(0, len(queries_all[cat_img][DOWNLOADER_RS]))
        self.assertEqual(1, len(queries_all[cat_vid_][DOWNLOADER_NM]))
        self.assertEqual(0, len(queries_all[cat_vid_][DOWNLOADER_RV]))
        self.assertEqual(0, len(queries_all[cat_vid_][DOWNLOADER_RC]))
        self.assertEqual(0, len(queries_all[cat_vid_][DOWNLOADER_RN]))
        self.assertEqual(0, len(queries_all[cat_vid_][DOWNLOADER_RX]))
        self.assertEqual(0, len(queries_all[cat_vid_][DOWNLOADER_RS]))
        self.assertEqual(
            f'python3 "D:/NM/src/ids.py" -start 1 -end 1 -path "../tests/{date_str_md(cat_vid)}/" --dump-tags -script "'
            'a: -quality 1080p -a -b -c -dfff ggg; '
            'b: -quality 1080p -a -b -c -dfff -ggg -(x,z) (h~i~j~k); '
            'c: -quality 1080p -a -b -c -dfff -ggg -h -i -j -k (l~m~n); '
            'd: -a -b -c -ggg -h -i -j -k -l -m -n -quality 360p -uvp always"',
            queries_all[cat_vid][DOWNLOADER_NM][0]
        )
        self.assertEqual(
            f'python3 "D:/old/RV/src/pages.py" -pages 5 -start 2 -stop_id 5 -begin_id 8 -path "../tests/{date_str_md(cat_vid)}/a/" '
            '-log info -timeout 15 -retries 50 -throttle 30 --dump-descriptions --dump-tags --dump-comments '
            '-quality 1080p -search a',
            queries_all[cat_vid][DOWNLOADER_RV][0]
        )
        self.assertEqual(
            f'python3 "D:/old/RV/src/pages.py" -pages 5 -start 2 -stop_id 5 -begin_id 8 -path "../tests/{date_str_md(cat_vid)}/b/" '
            '-log info -timeout 15 -retries 50 -throttle 30 --dump-descriptions --dump-tags --dump-comments '
            '-quality 1080p -search_tag b,c,d -search_rule_tag any',
            queries_all[cat_vid][DOWNLOADER_RV][1]
        )
        self.assertEqual(
            f'python3 "D:/old/RV/src/pages.py" -pages 5 -start 2 -stop_id 5 -begin_id 8 -path "../tests/{date_str_md(cat_vid)}/c/" '
            '-log info -timeout 15 -retries 50 -throttle 30 --dump-descriptions --dump-tags --dump-comments '
            '-quality 1080p -b -c -d -(g,h,i) -search_tag e,f -search_rule_tag all',
            queries_all[cat_vid][DOWNLOADER_RV][2]
        )
        self.assertEqual(
            f'python3 "D:/ruxx/src/ruxx_cmd.py" id:>=1 id:<=1 -path "../tests/{date_str_md(cat_img)}/a/" -module rx a',
            queries_all[cat_img][DOWNLOADER_RX][0]
        )
        self.assertEqual(
            f'python3 "D:/ruxx/src/ruxx_cmd.py" id:>=1 id:<=1 -path "../tests/{date_str_md(cat_img)}/b/" -module rx -a b (+c+~+d+)',
            queries_all[cat_img][DOWNLOADER_RX][1]
        )
        self.assertEqual(  # same dest for 'vid' and 'vid_' categories
            f'python3 "D:/NM/src/ids.py" -start 1 -end 1 -path "../tests/{date_str_md(cat_vid)}/" --dump-tags -script "'
            'a: -quality 1080p -a -b -c -dfff ggg; '
            'b: -quality 1080p -a -b -c -dfff -ggg -(x,z) (h~i~j~k)"',
            queries_all[cat_vid_][DOWNLOADER_NM][0]
        )
        print(f'{self._testMethodName} passed')

    def test_queries2(self) -> None:
        set_up_test()
        parse_arglist(args_argparse_str3.split())
        read_queries_file()
        prepare_queries()
        self.assertEqual('script_2', Config.title)
        self.assertEqual('P:/', Config.dest_base)
        self.assertEqual('P:/', Config.dest_bak_base)
        self.assertEqual('P:/', Config.dest_run_base)
        self.assertEqual('P:/', Config.dest_logs_base)
        print(f'{self._testMethodName} passed')

    def test_queries3(self) -> None:
        set_up_test()
        parse_arglist(args_argparse_str4.split())
        read_queries_file()
        self.assertRaises(AssertionError, prepare_queries)
        print(f'{self._testMethodName} passed')


class RunTests(TestCase):
    def test_main1(self) -> None:
        set_up_test()
        main_sync(('-script', '"../tests/queries.list"',
                   '--debug', '--no-download', '-downloaders', 'rx,nm,rn,rs'))
        print(f'{self._testMethodName} passed')

    def test_main2(self) -> None:
        set_up_test()
        main_sync(('-script', '"../tests/queries.list"',
                   '--debug', '-downloaders', 'rx,nm,rn,rs'))
        print(f'{self._testMethodName} passed')

    def test_main3(self) -> None:
        set_up_test()
        main_sync(('-script', '"../tests/queries.list"',
                   '-downloaders', 'rx,nm,rn,rs'))
        print(f'{self._testMethodName} passed')

#
#
#########################################
