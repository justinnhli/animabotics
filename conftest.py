"""PyTest configuration."""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any


SOURCE_PATH = Path(__file__).parent / 'animabotics'


def pytest_collection_modifyitems(session, config, items): # pylint: disable = unused-argument
    # type: (Any, Any, list[Any]) -> None
    """Sort tests by topological import order."""
    # group the tests by their paths
    num_items = len(items)
    tests = defaultdict(list)
    animabotics_test_path = SOURCE_PATH.parent / 'tests' / 'animabotics'
    for item in items:
        test_path_str, *_ = item.reportinfo()
        test_path = Path(test_path_str)
        if animabotics_test_path in test_path.parents:
            module = Path(test_path_str).relative_to(animabotics_test_path)
            module = module.with_stem(module.stem.replace('_test', ''))
        else:
            module = test_path
        tests[module].append(item)
    # collect the importees of of the source files
    modules = set()
    importees_of = defaultdict(set)
    importers_of = defaultdict(set)
    for source_path in SOURCE_PATH.glob('**/*.py'):
        importer = source_path.relative_to(SOURCE_PATH)
        modules.add(importer)
        with source_path.open(encoding='utf-8') as fd:
            for line in fd:
                match = re.fullmatch(r'from \.(\.*)([a-z0-9_]*) import .*', line.strip())
                if not match:
                    continue
                parent = source_path.parents[len(match.group(1))]
                if (parent / match.group(2)).is_dir():
                    importee_path = parent / match.group(2) / '__init__.py'
                else:
                    importee_path = parent / (match.group(2) + '.py')
                assert importee_path.is_file
                importee = importee_path.relative_to(SOURCE_PATH)
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
                del importees_of[importer]
        queue.extend(sorted(newly_ready))
    # add any non-matching tests at the end
    for value in tests.values():
        items.extend(value)
    assert len(items) == num_items
