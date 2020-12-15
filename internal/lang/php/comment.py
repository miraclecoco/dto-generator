from typing import List, Optional

from .phpdoc import Annotation


class Comment:
    def __init__(self, docstring: str = None, annotations: List[Annotation] = None) -> None:
        self._desc = docstring
        self._annotations = annotations

    def desc(self) -> Optional[str]:
        return self._desc

    def annotations(self) -> Optional[List[Annotation]]:
        return self._annotations

    def needs_generate(self) -> bool:
        return not not self.desc() or not not self.annotations()
