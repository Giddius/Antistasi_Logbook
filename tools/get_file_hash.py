
from pathlib import Path
from hashlib import blake2b, md5
from typing import Callable, Union
import os
import sys
FILE_HASH_INCREMENTAL_THRESHOLD: int = 52428800  # 50mb


def file_hash(in_file: Union[str, os.PathLike, Path], hash_algo: Callable = md5) -> str:
    in_file = Path(in_file)
    if not in_file.is_file():
        raise OSError(f"The path {in_file.as_posix()!r} either does not exist or is a Folder.")
    if in_file.stat().st_size > FILE_HASH_INCREMENTAL_THRESHOLD:
        _hash = hash_algo(usedforsecurity=False)
        with in_file.open("rb", buffering=FILE_HASH_INCREMENTAL_THRESHOLD // 4) as f:
            for chunk in f:
                _hash.update(chunk)
        return _hash.hexdigest()

    return hash_algo(in_file.read_bytes(), usedforsecurity=False).hexdigest()


if __name__ == '__main__':
    print(file_hash(sys.argv[1]))
