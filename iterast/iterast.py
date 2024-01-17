"""
Uses the AST of two versions of a program to figure out what changed, so you
can keep your REPL alive for longer.
"""
import ast
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from logger import get_logger

BASE_GLOBAL = globals()

logger = get_logger()


class Iterast(FileSystemEventHandler):
    def __init__(self, filename):
        self._filename = filename
        self._copies = []
        self._globals = None
        super().__init__()

    def reload(self):
        with open(self._filename) as f:
            self._copies.append(ast.parse(f.read()))
            self._copies = self._copies[-2:]
        if len(self._copies) == 1:
            self.evaluate(True, map(ast.unparse, self._copies[0].body))
            return

        reset, code = Iterast.get_actions(self._copies[0], self._copies[1])
        self.evaluate(reset, map(ast.unparse, code))

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

    def reset(self):
        self._globals = BASE_GLOBAL.copy()
        logger.info('[reset]')

    def evaluate(self, reset, code):
        if reset:
            self.reset()

        for line in code:
            line_str = line.split('\n')[0][:80]
            logger.info(f'[eval] {line_str}')
            try:
                exec(line, self._globals)
            except Exception as e:
                logger.error(f'[Exception] {e}')
                self.reset()
                break

    def dispatch(self, event):
        if not isinstance(event, FileModifiedEvent):
            return
        if event.src_path != self._filename:
            return
        self.reload()


def iterast_start(user_path):
    filename = os.path.abspath(user_path)

    event_handler = Iterast(filename)
    event_handler.reload()

    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(filename))
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
