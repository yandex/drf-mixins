import asyncio
import warnings
from collections import Counter
from contextlib import nullcontext
from typing import Any, ContextManager


class UnorderedList(list):
    def __eq__(self, other: Any) -> bool:
        if super().__eq__(other):
            return True
        try:
            return Counter(self) == Counter(other)
        except (TypeError, ValueError):
            try:
                return sorted(self) == sorted(other)
            except (TypeError, ValueError):
                remaining = list(other)
                try:
                    for element in self:
                        remaining.remove(element)
                except ValueError:
                    return False
                return not remaining


def num_queries_context(test_case: Any, num_queries: int | None) -> ContextManager:
    if num_queries is None:
        return nullcontext()
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return test_case.assertNumQueries(num_queries)

    warnings.warn(
        "num_queries is ignored in async context because assertNumQueries " "does not work correctly there",
        RuntimeWarning,
        stacklevel=3,
    )
    return nullcontext()
