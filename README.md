This is a small scripting engine that basically processes different r34 downloaders cmdlines in asynchronous manner (but only one query per downloader at a time). Use it if you want to create a periodic download system. Cmdline composition is based on simple syntax which allows to form series of cmdlines progressively and process multiple queries without creating duplicate files.

![c3](https://user-images.githubusercontent.com/76029665/203684613-3f11e0c9-1a42-4cb5-b56d-3da22b9cb219.gif)

Dependencies:
- Downloaders:
  - https://github.com/trickerer01/Ruxx
  - https://github.com/trickerer01/RV
  - https://github.com/trickerer01/NM
  - https://github.com/trickerer01/max-id-fetcher (optional)
- Libraries: None

See [SCRIPTING_SYNTAX.txt](https://github.com/trickerer01/download-multi-async-wrapper/blob/master/SCRIPTING_SYNTAX.txt) for script composition guidelines and tips  
Invoke `python main.py --help` to list cmdline arguments

Once you are done with initial script setup you only need to invoke a single cmd command to download the next batch without any need to even update next max id, ever (ideally)
