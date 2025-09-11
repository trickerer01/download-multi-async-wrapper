This is a small scripting engine that basically processes different r34 downloaders cmdlines in asynchronous manner (but only one query per downloader at a time). Use it if you want to create a periodic download system. Cmdline composition is based on simple syntax which allows to form series of cmdlines progressively and process multiple queries without creating duplicate files

![c3](https://user-images.githubusercontent.com/76029665/203684613-3f11e0c9-1a42-4cb5-b56d-3da22b9cb219.gif)

Dependencies:
- Python 3.10 or greater
- Downloaders:
  - https://github.com/trickerer01/Ruxx
  - https://github.com/trickerer01/RV
  - https://github.com/trickerer01/NM
  - https://github.com/trickerer01/RC
  - https://github.com/trickerer01/RG
  - Notes:
    - only downloaders listed within the script need to be cloned
- Libraries:
  - wrapper itself has no additional module dependencies
  - downloaders have their respective dependencies which have to be installed to the environment linked to Python executable path set within the script in order to enable wrapper to launch said downloaders. Check respective downloaders ReadMe's and `requirements.txt`. Use `--install` cmd argument to install enabled downloaders' dependencies to selected Python environment automatically. Notes:
    - RV, NM and RC dependencies are always the same
    - Ruxx dependencies are Python version dependent

See [SCRIPTING_SYNTAX.txt](https://github.com/trickerer01/download-multi-async-wrapper/blob/master/SCRIPTING_SYNTAX.txt) for script composition guidelines and tips  
Invoke `python main.py --help` to list all cmdline arguments

Once you are done with initial script setup you only need to invoke a single cmd command to download the next batch without any need to even update next max id manually, ever (ideally)
