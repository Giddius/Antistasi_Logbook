from pathlib import Path
import os


base_path = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook")


def gg():
    for dirname, folderlist, filelist in os.walk(base_path):
        for _file in filelist:
            file = Path(dirname, _file)
            if "apsw" in file.stem.casefold():
                yield file


for i in gg():
    print(i.as_posix())
