from typing import List, Callable, Optional
from abc import ABC, abstractmethod
from copy import copy

from internal.codegen.common.util import ListCollection


class IndentStyle:
    def __init__(self, filler: str, span: int):
        self._filler = filler
        self._span = span

    @staticmethod
    def tab(span: int) -> 'IndentStyle':
        return IndentStyle("\t", span)

    @staticmethod
    def space() -> 'IndentStyle':
        return IndentStyle(" ", 1)

    @staticmethod
    def none() -> 'IndentStyle':
        return IndentStyle("", 1)

    def process(self, size: int) -> str:
        multiple = size // self._span
        return self._filler * multiple


class Indent:
    def __init__(self, size: int, style: IndentStyle):
        self._size = size
        self._style = style

    def process(self, n: int) -> str:
        return self._style.process(self._size * n)


class PrinterConfig:
    def __init__(self, indent: Indent):
        self._indent = indent

    @staticmethod
    def default() -> 'PrinterConfig':
        return PrinterConfig(Indent(4, IndentStyle.space()))

    def indent(self) -> Indent:
        return self._indent

    def clone(self) -> 'PrinterConfig':
        return PrinterConfig(self._indent)


class Printer(ABC):
    def __init__(self, parent: 'Printer' = None, children: List['PrinterFactory'] = None):
        if children is None:
            children = []

        self._parent = parent
        self._children = children
        self._children_cache = None

    def parent(self) -> Optional['Printer']:
        return self._parent

    def children(self) -> List['Printer']:
        return self._resolve_children()

    def match_child(self, fn: Callable[['Printer'], bool]) -> Optional['Printer']:
        return ListCollection(self.children()).single(fn)

    def match_children(self, fn: Callable[['Printer'], bool]) -> List['Printer']:
        return ListCollection(self.children()).filter(fn).elements()

    @abstractmethod
    def do_print(self, context: 'PrintContext') -> str:
        pass

    def print(self, context: 'PrintContext') -> str:
        context.set_printer(self)

        for middleware in context.middlewares():
            middleware.configure_context(context)

        result = self.do_print(context)

        for middleware in context.middlewares():
            result = middleware.transform(context, result)

        return result

    def _resolve_children(self) -> List['Printer']:
        if self._children_cache is None:
            self._children_cache = [factory.create_printer(self) for factory in self._children]

        return self._children_cache


class PrinterFactory(ABC):
    #
    # this method will be executed in parent printer in common
    @abstractmethod
    def create_printer(self, parent: Printer) -> Printer:
        pass


class PrinterMiddleware:
    def configure_context(self, context: 'PrintContext') -> None:
        pass

    def configure_child_context(self, context: 'PrintContext', rule: 'PrintStateTransitionRule') -> None:
        pass

    def transform(self, context: 'PrintContext', content: str) -> str:
        return content


class PrintState:
    def __init__(self, parent: Optional['PrintState'], indent_size: int):
        self._parent = parent
        self._indent_size = indent_size

    @staticmethod
    def initial() -> 'PrintState':
        return PrintState(None, 0)

    def parent(self) -> Optional['PrintState']:
        return self._parent

    def indent_size(self) -> int:
        return self._indent_size

    def set_indent_size(self, indent_size: int) -> None:
        self._indent_size = indent_size

    def clone(self) -> 'PrintState':
        return PrintState(self._parent, self._indent_size)


class PrintStateGenerator:
    @staticmethod
    def default():
        return PrintStateGenerator()

    def generate(self, previous_state: PrintState, rule: 'PrintStateTransitionRule' = None) -> PrintState:
        if rule is None:
            rule = PrintStateTransitionRule.keep()

        rule.apply(previous_state)

        return previous_state.clone()


class PrintStateTransitionRule:
    def __init__(self):
        pass

    @staticmethod
    def keep() -> 'PrintStateTransitionRule':
        return PrintStateTransitionRule()

    def apply(self, state: 'PrintState') -> None:
        pass


class PrintContext:
    def __init__(self, parent: Optional['PrintContext'], config: PrinterConfig = None,
                 middlewares: List[PrinterMiddleware] = None, state_generator: PrintStateGenerator = None,
                 state: PrintState = None):
        if parent is None:
            if state_generator is None:
                state_generator = PrintStateGenerator.default()
            if state is None:
                state = PrintState.initial()

        self._parent = parent
        self._config = config
        self._middlewares = middlewares
        self._state_generator = state_generator
        self._state = state
        self._printer = None

    @staticmethod
    def initial(config: PrinterConfig, middlewares: List[PrinterMiddleware] = None) -> 'PrintContext':
        return PrintContext(None, config, middlewares)

    def parent(self) -> Optional['PrintContext']:
        return self._parent

    def config(self) -> PrinterConfig:
        return self._config if self._config is not None else self.parent().config()

    def set_config(self, config: PrinterConfig):
        self._config = config

    def middlewares(self) -> List[PrinterMiddleware]:
        return copy(self._middlewares) if self._middlewares is not None else self.parent().middlewares()

    def add_middleware(self, *middlewares: List[PrinterMiddleware]) -> None:
        if len(middlewares) == 0:
            return

        if self._middlewares is None:
            self._middlewares = []

        self._middlewares.extend(middlewares)

    def state_generator(self) -> PrintStateGenerator:
        return self._state_generator if self._state_generator is not None else self.parent().state_generator()

    def set_state_generator(self, state_generator: PrintStateGenerator) -> None:
        self._state_generator = state_generator

    def state(self) -> PrintState:
        return self._state

    def set_state(self, state: PrintState) -> None:
        self._state = state

    def printer(self) -> Printer:
        return self._printer

    def set_printer(self, printer: Printer) -> None:
        self._printer = printer

    def stack(self) -> List[Printer]:
        stack = []
        current = self

        while current is not None:
            stack.append(current.printer())
            current = current.parent()

        return stack

    def clone(self) -> 'PrintContext':
        return PrintContext(self._parent, self._config, self._middlewares, self._state_generator, self._state)

    def create_child(self, configure: Callable[['PrintContext'], None] = None,
                     rule: PrintStateTransitionRule = None) -> 'PrintContext':
        child_state = self.state_generator().generate(self.state(), rule)
        child = PrintContext(self, None, None, None, child_state)

        for middleware in self.middlewares():
            middleware.configure_child_context(child, rule)

        if configure is not None:
            configure(child)

        return child


class HighOrderPrinter(Printer):
    def __init__(self, print_fn: Callable[[Printer, PrintContext], str], parent: Printer = None,
                 children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._print_fn = print_fn

    def do_print(self, context: PrintContext) -> str:
        return self._print_fn(self, context)


class PassThroughPrinter(Printer):
    def do_print(self, context: PrintContext) -> str:
        if len(self.children()) > 1:
            raise ValueError('expect 1 child, but {0} children is given', len(self.children()))

        return self.children()[0].print(context.create_child())


class PassThroughManyPrinter(Printer):
    def __init__(self, print_fn: Callable[[List[str]], str], parent: Printer = None,
                 children: List[PrinterFactory] = None):
        super().__init__(parent, children)

        self._print_fn = print_fn

    def do_print(self, context: PrintContext) -> str:
        contents = [printer.print(context.create_child()) for printer in self.children()]

        return self._print_fn(contents)
