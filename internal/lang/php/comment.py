from typing import List, Optional

from .annotation import Annotation


class Comment:
    def __init__(self, docstring: str = None, annotations: List[Annotation] = None) -> None:
        self._docstring = docstring
        self._annotations = annotations

    def docstring(self) -> Optional[str]:
        return self._docstring

    def annotations(self) -> Optional[List[Annotation]]:
        return self._annotations

    def needs_generate(self) -> bool:
        return self.docstring() is not None or self.annotations() is not None
