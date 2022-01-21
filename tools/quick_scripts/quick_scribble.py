import sys
import os
import shutil

x = {}

for i in range(100):
    x[str(i)] = i

print(sys.getsizeof(x))
