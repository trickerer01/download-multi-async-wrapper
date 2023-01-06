This is an engine that basically processes  different r34 downloaders cmdlines in asynchronous manner (but one query per downloader at a time). Cmdline composition is based on a simple syntax which allows to form series of cmdlines progressively and process multiple queries without creating duplicates

Ruxx, RV and NM downloaders are all supported  
See [SCRIPTING_SYNTAX.txt](https://github.com/trickerer01/download-multi-async-wrapper/blob/master/SCRIPTING_SYNTAX.txt) for script composition guidelines  
Invoke `python main.py --help` to list config arguments

Dependencies:
- https://github.com/trickerer01/Ruxx
- https://github.com/trickerer01/RV
- https://github.com/trickerer01/NM

Optional dependency:
- https://github.com/trickerer01/max-id-fetcher  

Tiny preview:  
![c3](https://user-images.githubusercontent.com/76029665/203684613-3f11e0c9-1a42-4cb5-b56d-3da22b9cb219.gif)
