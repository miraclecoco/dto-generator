from internal.codegen.printer import PrinterMiddleware


class Formatter(PrinterMiddleware):
    def configure_context(self):
        pass

    def after_print(self):
        pass
