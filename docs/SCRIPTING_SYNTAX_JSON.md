Here is a JSON representation of improvised script explaining every statement and overall cmdline composition process  
**If you need a base json script to build upon look in examples folder**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "$comment": "Test script ver 1.0",
  "title": "script_0", "$comment": "Script title (used in log and run file names as a suffix, 1-20 symbols)",
  "title_increment": "4", "$comment": "Script run number automatic increment suffix length, 1-9, here it's 0001, 0002, etc.",
  "dest_path": "../dest", "$comment": "Download destination base folder, default: './'. Can be used instead of '-path' cmd argument (but not both)",
  "bak_path": "../bak", "$comment": "Script backup folder, saved before update (see below), default: './'",
  "run_path": "../run", "$comment": "Run files destination folder, used when downloader cmdline is too long, default: './'",
  "log_path": "../logs", "$comment": "Log files destination folder, logs will be saved to disk always, default: './'",
  "date_sub": "YES", "$comment": "Date subfolder '/MMDD/' in base dest folder creation flag, default: 'yes'. Can also use other values: 'False', 'True', 'no', 'yes', 'n', 'y', '0', '1', etc.",
  "update": "YES", "$comment": "ID range (see below) update with fetched max id flag, default: 'no'",
  "update_offsets": {
    "NM": -100,
    "rc": -100,
    "RV": -800,
    "RS": -300
  }, "$comment": "Max id update offset per downloader (usually negative). If update flag is set the script gets updated with current max id per downloader for the next run. This value offsets maximum id so next time more (or less) ids are covered. Can be left empty",
  "noproxy_fetches": [
    "rg",
    "nm"
  ], "$comment": "Downloaders for which max id is always fetched without proxy even if provided",
  "python": "python3", "$comment": "Path to python executable (normally root python install is present in system path variable)",
  "compose": { "$comment": "Script body starts here",
    "VIDEOS": { "$comment": "Category marker, at least 1 symbol (subfolder name: 'VIDEOS')",
      "NM": { "$comment": "Downloader type (downloader NM within VIDEOS category",
        "downloader": "D:/Projects/NM", "$comment": "Path to the downloader base folder",
        "pages": null, "$comment": "[can be null] Switch to pages scan instead of ids (pages count, [optional] starting page), see below",
        "ids": ["50000", "51000"], "$comment": "At least one or two ids for range (see below)",
        "common": [
          "-dmode touch",
          "-log trace --dump-tags"
        ], "$comment": "Arguments to add to every query",
        "subs": [
          { "$comment": "Each sub contains subfolder name and cmdline arguments to increment upon",
            "a": [ { "$comment": "Subfolder name (new query marker)" },
              "-quality 1080p", { "$comment": "[downloader arguments] Sub argument (quality)" },
              "-a -b -c -dfff", { "$comment": "[downloader arguments] Excluded tags" },
              "ggg", { "$comment": "[downloader arguments] Required tag" }
            ], "$comment": "At least one 'tags' argument is required for query to be valid. Mixing of required / excluded tags in a row is not recommended: '-a -b -c -dfff ggg'"
          },
          { "$comment": "'<cmdline base...> -quality 1080p -a -b -c -dfff ggg'" },
          { "$comment": "Downloader arguments still accumulate after this, see below" },
          {
            "b": [ { "$comment": "Second subfolder name (new query marker)" },
              "-ggg", { "$comment": "Remove previous tag and exclude it (removes from downloader arguments list)" },
              "-(x,z)", { "$comment": "Excluded tags combination" },
              "(h~i~j~k)", { "$comment": "Required 'or' group or tags ('any of')" }
            ]
          },
          { "$comment": "'<cmdline base...> -quality 1080p -a -b -c -dfff -ggg -(x,z) (h~i~j~k)'" },
          {
            "c": [
              "-h -i -j -k", {
                "$comment": [
                  "Remove previous tags group and exclude them (removes from downloader arguments list)",
                  "Must match previous group exactly otherwise you get something like '(h~i~j~k~l) -h -i -j -k'",
                  "Logs will mention multiple exclusions like this where matching 'or' group wasn't found"
                ]
              },
              "--(x,z)", { "$comment": "Remove previously excluded tags combination (removes from downloader arguments list)" },
              "(l~m~n)", { "$comment": "Sub connot consist of only negative tags" }
            ]
          },
          { "$comment": "'<cmdline base...> -quality 1080p -a -b -c -dfff -ggg -h -i -j -k (l~m~n)'" },
          {
            "d": [
              "--quality -+1080p", { "$comment": "Remove previous param ('-quality 1080p') query argument (removes from downloader arguments list)" },
              "-l -m -n",
              "--dfff",
              "-quality 360p",
              "-uvp always"
            ]
          },
          { "$comment": "'<cmdline base...> -a -b -c -ggg -h -i -j -k -l -m -n -quality 360p -utp always'" }
        ]
      },
      "$comment": [
        "At this point 4 nm queries were created which will be then combined into a single download script",
        "'python \"D:/projects/nm/src/ids.py\" -path \"<path>\" -start 50000 -end 50999",
        "-dmode touch -log trace --dump-tags -script",
        "\"a: -quality 1080p -a -b -c -dfff ggg;",
        "b: -quality 1080p -a -b -c -dfff -ggg -(x,z) (h~i~j~k);",
        "c: -quality 1080p -a -b -c -dfff -ggg -h -i -j -k (l~m~n);",
        "d: -a -b -c -ggg -h -i -j -k -l -m -n -quality 360p -utp always\"'",
        "which downloads matching videos to 4 different folders in a single pass"
      ],
      "rv": { "$comment": "Downloader name is case-insensitive",
        "pages": ["p10 s1"], "$comment": "[optional] Switch to pages scan instead of ids (pages count, starting page can be omitted)",
        "ids": ["9000"], "$comment": "A single id means from this id and up (till current max id)",
        "downloader": "D:/Projects/RV",
        "common": [
          "-log info -timeout 30 -retries 100 -throttle 100"
        ],
        "subs": [
          {
            "a": [
              "-quality 1080p",
              "-search aaa", { "$comment": "[downloader arguments] Use search string" }
            ]
          },
          { "$comment": "'<cmdline base...> -quality 1080p -search aaa'" },
          {
            "b": [
              { "$comment": "'--search -+aaa' is one way to remove previous search argument but there is a shorter version" },
              "-aaa", { "$comment": "Quicker way to remove previous search argument (removes from downloader arguments list, doesn't exclude)" },
              "-search_tag tag1,tag2,tag3",
              "-search_rule_tag any"
            ]
          },
          { "$comment": "'<cmdline base...> -quality 1080p -search_tag tag1,tag2,tag3 -search_rule_tag any'" },
          {
            "c": [
              "-any",
              "-tag1 -tag2 -tag3", { "$comment": "Quickly remove previous search tags (removes from downloader arguments list) and exclude them (adds to downloader arguments list). Exclusion is caused by the number of tags being greater than one" },
              "-search_tag tag4,tag5", { "$comment": "[downloader arguments] Search for 2 different tags"},
              "-search_rule_tag all"
            ]
          },
          { "$comment": "'<cmdline base...> -quality 1080p -tag1 -tag2 -tag3 -search_tag tag4,tag5 -search_rule_tag all'" }
        ]
      },
      "$comment": [
        "At this point 3 rv queries were created which will not be optimized because of search being used",
        "'python \"D:/projects/rv/src/ids.py\" -pages 10 -start 1 -stop_id 9000 -begin_id <fetched_max_id>",
        "-path \"/a\" -log info -timeout 30 -retries 100 -throttle 100 --dump-descriptions --dump-tags",
        "-quality 1080p -search aaa'",
        "'python \"d:/projects/rv/src/ids.py\" -pages 10 -start 1 -stop_id 9000 -begin_id <fetched_max_id>",
        "-path \"/b\" -log info -timeout 30 -retries 100 -throttle 100 --dump-descriptions --dump-tags",
        "-quality 1080p -search_tag tag1,tag2,tag3 -search_rule_tag any'",
        "'python \"d:/projects/rv/src/ids.py\" -pages 10 -start 1 -stop_id 9000 -begin_id <fetched_max_id>",
        "-path \"/c\" -log info -timeout 30 -retries 100 -throttle 100 --dump-descriptions --dump-tags",
        "-quality 1080p -tag1 -tag2 -tag3 -search_tag tag4,tag5 -search_rule_tag all'"
      ],
      "rn": {
        "pages": null,
        "ids": ["-10000"], "$comment": "A single negative id means 'last x posts'",
        "downloader": "D:/Projects/Ruxx",
        "common": [ "..." ],
        "subs": [ "..." ]
      }
    },
    "IMAGES": { "$comment": "Second category marker (subfolder name: 'IMAGES')",
      "rx": "...",
      "rp": "...",
      "xb": "..."
    },
    "VIDEOS ": { "$comment": "Third category marker. Trailing space allows to download to the same folder as first category (subfolder name: 'VIDEOS')",
      "": "..."
    }
  }
}
```
