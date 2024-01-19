"""
Uses the AST of two versions of a program to figure out what changed, so you
can keep your REPL alive for longer.
"""
import ast
import time
import os
import sys
import importlib
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from logger import get_logger

BASE_GLOBAL = globals()
MODULE_PATH = sys.path

logger = get_logger()


class FindImports(ast.NodeVisitor):
    def __init__(self):
        self._modules = []

    def modules(self):
        return self._modules

    def visit_Import(self, node):
        self._modules += list(map(lambda x: x.name, node.names))

    def visit_ImportFrom(self, node):
        self._modules.append(node.module)


class Iterast(FileSystemEventHandler):
    def __init__(self, filename, clear=True):
        self._filename = filename
        self._copies = []
        self._globals = None
        self._module_files = []
        self._clear = clear
        super().__init__()

        self.reload()

    def reload(self, reeval=False):
        with open(self._filename) as f:
            parsed = ast.parse(f.read())

        # extracting the modules from the file
        self._modules = Iterast.find_module_paths(parsed)

        self._copies.append(parsed)
        self._copies = self._copies[-2:]

        if len(self._copies) == 1 or reeval:
            self.reset()
            self.evaluate(map(ast.unparse, self._copies[-1].body))
            return

        reset, code = Iterast.get_actions(self._copies[0], self._copies[1])
        if reset:
            self.reset()
        self.evaluate(map(ast.unparse, code))

    @staticmethod
    def find_module_paths(ast):
        fi = FindImports()
        fi.visit(ast)
        return fi.modules()

    @staticmethod
    def get_actions(ap, bp):
        apb = ap.body
        bpb = bp.body
        found_diff = False
        to_evaluate = []

        if len(apb) > len(bpb):
            to_evaluate = bpb
            return (True, to_evaluate)

        # Discover if something earlier in the code changed.
        for a, b in zip(apb, bpb):
            if found_diff:
                to_evaluate.append(b)
                continue

            if Iterast.diff_ast(a, b):
                found_diff = True
                to_evaluate.append(b)

        # If there is any new code, we have to evaluate it.
        if len(bpb) > len(apb):
            to_evaluate += bpb[len(apb):]

        return (False, to_evaluate)

    @staticmethod
    def diff_ast(a, b):
        """
        Check if two ast trees differ, and if so, return true.
        """
        return ast.unparse(a) != ast.unparse(b)

    def reload_module(self, module):
        logger.info(f'[reload] {module}')
        if not module and module in self._globals:
            return

        if module not in self._globals:
            return

        importlib.reload(self._globals[module])

    def reset(self, error=False):
        if self._clear and not error:
            os.system('cls' if os.name == 'nt' else 'clear')
        logger.info('[reset]')
        if error:
            return
        self._globals = BASE_GLOBAL.copy()
        self._globals['__name__'] = '__main__'
        self._globals['sys'].path = [os.path.dirname(self._filename)] + \
            MODULE_PATH

    def evaluate(self, code):
        for line in code:
            line_str = line.split('\n')[0][:80]
            logger.info(f'[eval] {line_str}')
            try:
                exec(line, self._globals)
            except Exception as e:
                logger.error(f'[Exception] {e}')
                self.reset(error=True)
                break

    def dispatch(self, event):
        match event:
            case FileModifiedEvent():
                basename = os.path.basename(event.src_path).split('.')[0]
                if event.src_path == self._filename:
                    self.reload()
                elif basename in self._modules:
                    self.reload_module(basename)
                    self.reload(reeval=True)


def iterast_start(user_path, clear):
    filename = os.path.abspath(user_path)
    os.chdir(os.path.dirname(filename))

    event_handler = Iterast(filename, clear=clear)

    def signal_handler(sig, frame):
        event_handler.reload(True)

    signal.signal(signal.SIGQUIT, signal_handler)

    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(filename))
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
