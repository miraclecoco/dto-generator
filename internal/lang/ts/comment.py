from typing import List, Optional

from .typedoc import Annotation


class Comment:
    def __init__(self, desc: str = None, annotations: List[Annotation] = None) -> None:
        self._decs = desc
        self._annotations = annotations

    def desc(self) -> Optional[str]:
        return self._decs

    def annotations(self) -> Optional[List[Annotation]]:
        return self._annotations

    def needs_generate(self) -> bool:
        return not not self.desc() or not not self.annotations()
