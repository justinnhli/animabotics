"""Utilities for memory profiling."""

import gc
import linecache
import os
from tracemalloc import Snapshot, Filter
from collections import namedtuple
from json import load as json_read, dump as json_write
from pathlib import Path
from sys import getsizeof

MemoryObject = namedtuple('MemoryObject', 'id, classname, size, referrers, referents')

STATM_PATH = Path('/proc/self/statm')


def get_memory_usage():
    # type: () -> int
    """Get the total memory usage, in kB"""
    return int(STATM_PATH.read_text(encoding='utf-8').split(maxsplit=1)[0])


def dump_memory(filepath):
    # type: (Path) -> None
    """Dump all memory objects to file."""
    objects = []
    for obj in list(gc.get_objects()):
        if not hasattr(obj, '__class__'):
            continue
        objects.append(MemoryObject(
            id(obj),
            str(obj.__class__),
            getsizeof(obj, 0),
            [
                id(o) for o in gc.get_referrers(obj)
                if hasattr(o, '__class__')
            ],
            [
                id(o) for o in gc.get_referents(obj)
                if hasattr(o, '__class__')
            ],
        ))
    with filepath.open('w') as fd:
        json_write(objects, fd)


def read_memory_dump(filepath):
    # type: (Path) -> list[MemoryObject]
    """Read a memory dump."""
    with filepath.open('rb') as fd:
        return [MemoryObject(*args) for args in json_read(fd)]


def display_top(snapshot, key_type='lineno', limit=10):
    # type: (Snapshot, str, int) -> None
    """Display top memory allocations from tracemalloc.take_snapshot()."""
    # from https://docs.python.org/dev/library/tracemalloc.html
    snapshot = snapshot.filter_traces((
        Filter(False, '<frozen importlib._bootstrap>'),
        Filter(False, '<unknown>'),
    ))
    top_stats = snapshot.statistics(key_type)
    print(f'Top {limit} lines')
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print(f'#{index}: {filename}:{frame.lineno}: {stat.size / 1024:.1f} KiB')
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print(f'    {line}')
    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print(f'{len(other)} other: {size / 1024:.1f} KiB')
    total = sum(stat.size for stat in top_stats)
    print(f'Total allocated size: {total / 2014:.1f} KiB')
