import queue
from typing import Optional, List


class RK800CommandQueue:

    def __init__(self, ctx):
        self.ctx = ctx
        self.command_queue = queue.Queue()
        self.results_queue = queue.Queue()

    def add_command(self, cmd):
        self.command_queue.put(cmd)
        self.ctx.view.success(f"queued: {cmd.line}")

    def get_next_command(self):
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None

    def add_result(self, result):
        self.results_queue.put(result)

    def drain_results(self) -> List[str]:
        """Get all results and clear the queue"""
        results = []
        while True:
            try:
                results.append(self.results_queue.get_nowait())
            except queue.Empty:
                break
        return results

    def status(self):
        return {
            "commands": self.command_queue.qsize(),
            "results": self.results_queue.qsize(),
        }
