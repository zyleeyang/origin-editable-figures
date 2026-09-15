"""Own one external Origin instance; close it before writing verification files.

Use in a fresh Python process, before any originpro call starts/attaches Origin.
Never terminates processes or attaches to an existing Origin application.
"""

import ctypes
from ctypes import wintypes
import json
import os
import sys


class _ProcessWatch:
    """Wait on the exact process handle, avoiding PID reuse and process-list races."""

    def __init__(self, pid):
        if sys.platform != 'win32' or pid <= 0 or pid == os.getpid():
            raise RuntimeError('Origin did not return a valid Windows process ID.')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        # SYNCHRONIZE only: no terminate/write permissions.
        self.handle = self.kernel.OpenProcess(0x100000, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def wait(self, seconds):
        result = self.kernel.WaitForSingleObject(self.handle, int(seconds * 1000))
        if result == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error())
        return result == 0  # WAIT_OBJECT_0; WAIT_TIMEOUT is not successful cleanup.

    def close(self):
        self.kernel.CloseHandle(self.handle)


class OwnedOrigin:
    """Close only our independent Application, including on exceptions/Ctrl+C.

    Save and reopen output files inside the with block. Never attach(), detach(),
    exit(), or replace the originpro connection within that block. The default
    close discards this disposable instance's unsaved changes, not saved files.
    Abrupt Python termination or a hung COM call cannot be caught by this helper.
    """

    def __init__(self, op, *, report=None, report_path=None, timeout=15):
        if not 0 < timeout <= 60:
            raise ValueError('Exit verification timeout must be within 0..60 seconds.')
        self.op = op
        self.report = report if report is not None else {}
        self.report_path = report_path
        self.timeout = timeout
        self.app = None
        self.watch = None
        self.finished = False
        self.entered = False
        self.state = {'mode': 'independent', 'pid': None, 'exit_verified': False}

    def __enter__(self):
        if self.entered:
            raise RuntimeError('OwnedOrigin is single-use; create a new context manager for each session.')
        # originpro 1.1.x stores its external Application in this lazy wrapper.
        # Check without accessing lazy attributes, which could start an instance.
        if not self.op.oext or '_app' not in vars(self.op.po):
            raise RuntimeError('Use a fresh external Python process with a supported originpro wrapper.')
        if vars(self.op.po)['_app'] is not None:
            raise RuntimeError('An Origin connection already exists in this Python process; refusing to use or close it.')
        self.entered = True
        self.report['origin_session'] = self.state
        try:
            self.op.set_show(False)
            self.app = vars(self.op.po)['_app']
            if self.app is None:
                raise RuntimeError('Origin did not create an independent Application.')
            # Execute inside OUR Origin application, not in the external Python
            # interpreter. No PID guessing from a global before/after snapshot.
            self.op.lt_exec("run -py __import__('PyOrigin').LT_set_var('SkillProcessId', __import__('os').getpid());")
            self.state['pid'] = self.op.lt_int('SkillProcessId')
            self.watch = _ProcessWatch(self.state['pid'])
        except BaseException as error:
            # set_show may fail after creating the Application.
            if self.app is None:
                self.app = vars(self.op.po)['_app']
            self._finish(error)
            raise
        return self

    def _close(self):
        try:
            if self.app is not None:
                # Retain the exact owned COM object, even if caller code changed
                # the global wrapper. Do not call a lazy op API after exiting.
                self.app.Exit()
                if vars(self.op.po).get('_app') is self.app:
                    self.op.po._app = None
                self.app = None
                if self.watch is None:
                    raise RuntimeError('Origin exit requested, but its process could not be verified.')
                self.state['exit_verified'] = self.watch.wait(self.timeout)
                if not self.state['exit_verified']:
                    raise RuntimeError(f"Origin PID {self.state['pid']} did not exit within {self.timeout}s; no process was forcibly terminated.")
        finally:
            if self.watch is not None:
                self.watch.close()
                self.watch = None

    def _finish(self, primary_error):
        if self.finished:
            return
        self.finished = True
        secondary = []
        try:
            self._close()
        except BaseException as error:
            self.state['cleanup_error'] = f'{type(error).__name__}: {error}'
            secondary.append(error)
        self.report['task_status'] = 'failed' if primary_error or secondary else 'completed'
        if primary_error is not None:
            self.report['error'] = f'{type(primary_error).__name__}: {primary_error}'
        # Filesystem errors must never prevent Origin cleanup.
        if self.report_path is not None:
            try:
                self.report_path.parent.mkdir(parents=True, exist_ok=True)
                self.report_path.write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding='utf-8')
            except BaseException as error:
                self.report['task_status'] = 'failed'
                secondary.append(error)
        if primary_error is not None:
            for error in secondary:
                print(f'Additional Origin cleanup/report error: {error}', file=sys.stderr)
                if hasattr(primary_error, 'add_note'):
                    primary_error.add_note(f'Additional cleanup/report error: {error}')
        elif secondary:
            for error in secondary[1:]:
                print(f'Additional verification report error: {error}', file=sys.stderr)
            raise secondary[0]

    def __exit__(self, exc_type, exc_value, traceback):
        self._finish(exc_value)
        return False
