"""PyTest configuration."""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any


SOURCE_PATH = Path(__file__).parent / 'dumpy'


def pytest_collection_modifyitems(session, config, items): # pylint: disable = unused-argument
    # type: (Any, Any, list[Any]) -> None
    """Sort tests by topological import order."""
    # group the tests by their paths
    num_items = len(items)
    tests = defaultdict(list)
    for item in items:
        test_path, *_ = item.reportinfo()
        module = test_path.stem.replace('_test', '')
        tests[module].append(item)
    # collect the importees of of the source files
    modules = set()
    importees_of = defaultdict(set)
    importers_of = defaultdict(set)
    for source_path in SOURCE_PATH.glob('*.py'):
        importer = source_path.stem
        modules.add(importer)
        with source_path.open(encoding='utf-8') as fd:
            for line in fd:
                match = re.fullmatch(r'from \.([a-z0-9_]*) import .*', line.strip())
                if not match:
                    continue
                importee = match.group(1)
                importees_of[importer].add(importee)
                importers_of[importee].add(importer)
    # re-add tests in topological order
    items.clear()
    queue = sorted(modules - set(importees_of.keys()))
    while queue:
        importee = queue.pop(0)
        if importee in tests:
            items.extend(tests.pop(importee))
        newly_ready = set()
        for importer in sorted(importers_of.get(importee, set())):
            importees_of[importer].remove(importee)
            if not importees_of[importer]:
                newly_ready.add(importer)
        queue.extend(sorted(newly_ready))
    # add any non-matching tests at the end
    for value in tests.values():
        items.extend(value)
    assert len(items) == num_items
