"""Failure-path regression tests; no Origin installation is needed."""

from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from origin_session import OwnedOrigin


class App:
    def __init__(self):
        self.exits = 0

    def Exit(self):
        self.exits += 1


class FakeOrigin:
    def __init__(self):
        self.oext = True
        self.po = SimpleNamespace(_app=None)
        self.created = App()

    def set_show(self, visible):
        self.po._app = self.created

    def lt_exec(self, command):
        pass

    def lt_int(self, name):
        return 123


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.op = FakeOrigin()
        self.watcher_patch = patch('origin_session._ProcessWatch')
        self.watcher = self.watcher_patch.start().return_value
        self.watcher.wait.return_value = True
        self.addCleanup(self.watcher_patch.stop)

    def test_success_closes_before_report_write(self):
        report = {}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'report.json'
            def write_after_exit(*args, **kwargs):
                self.assertEqual(self.op.created.exits, 1)
                self.assertTrue(report['origin_session']['exit_verified'])
            with patch.object(Path, 'write_text', side_effect=write_after_exit):
                with OwnedOrigin(self.op, report=report, report_path=path):
                    pass
        self.assertEqual(report['task_status'], 'completed')
        self.assertIsNone(self.op.po._app)

    def test_disk_error_still_closes_and_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(Path, 'write_text', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(OSError, 'disk full'):
                    with OwnedOrigin(self.op, report_path=Path(folder)/'report.json'):
                        pass
        self.assertEqual(self.op.created.exits, 1)
        self.watcher.wait.assert_called_once()

    def test_body_errors_and_interrupts_close(self):
        for error in (ValueError('plot failed'), KeyboardInterrupt(), SystemExit(2)):
            with self.subTest(error=type(error).__name__):
                op = FakeOrigin()
                with self.assertRaises(type(error)) as captured:
                    with OwnedOrigin(op):
                        raise error
                self.assertIs(captured.exception, error)
                self.assertEqual(op.created.exits, 1)

    def test_existing_connection_is_untouched(self):
        self.op.po._app = self.op.created
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            with OwnedOrigin(self.op):
                self.fail('Must not enter existing session')
        self.assertEqual(self.op.created.exits, 0)

    def test_embedded_origin_is_untouched(self):
        self.op.oext = False
        with self.assertRaisesRegex(RuntimeError, 'external Python'):
            with OwnedOrigin(self.op):
                pass
        self.assertEqual(self.op.created.exits, 0)

    def test_start_failure_after_creation_closes(self):
        def fail_after_start(visible):
            self.op.po._app = self.op.created
            raise ValueError('visibility failed')
        self.op.set_show = fail_after_start
        with self.assertRaisesRegex(ValueError, 'visibility failed'):
            with OwnedOrigin(self.op):
                pass
        self.assertEqual(self.op.created.exits, 1)

    def test_pid_lookup_failure_closes(self):
        self.op.lt_int = lambda name: (_ for _ in ()).throw(ValueError('no PID'))
        with self.assertRaisesRegex(ValueError, 'no PID'):
            with OwnedOrigin(self.op):
                pass
        self.assertEqual(self.op.created.exits, 1)

    def test_exit_timeout_fails_instead_of_reporting_success(self):
        self.watcher.wait.return_value = False
        report = {}
        with self.assertRaisesRegex(RuntimeError, 'did not exit'):
            with OwnedOrigin(self.op, report=report):
                pass
        self.assertEqual(report['task_status'], 'failed')
        self.assertFalse(report['origin_session']['exit_verified'])

    def test_exit_exception_is_not_swallowed(self):
        self.op.created.Exit = lambda: (_ for _ in ()).throw(OSError('COM exit failed'))
        with self.assertRaisesRegex(OSError, 'COM exit failed'):
            with OwnedOrigin(self.op):
                pass
        self.watcher.close.assert_called_once()

    def test_cleanup_failure_does_not_hide_body_failure(self):
        self.watcher.wait.return_value = False
        error = ValueError('original plot failure')
        with self.assertRaises(ValueError) as captured:
            with OwnedOrigin(self.op):
                raise error
        self.assertIs(captured.exception, error)

    def test_replaced_global_connection_is_not_closed(self):
        unrelated = App()
        with OwnedOrigin(self.op):
            self.op.po._app = unrelated
        self.assertEqual(self.op.created.exits, 1)
        self.assertEqual(unrelated.exits, 0)
        self.assertIs(self.op.po._app, unrelated)

    def test_context_cannot_be_reused_to_leak_a_second_instance(self):
        session = OwnedOrigin(self.op)
        with session:
            pass
        with self.assertRaisesRegex(RuntimeError, 'single-use'):
            with session:
                pass
        self.assertIsNone(self.op.po._app)
        self.assertEqual(self.op.created.exits, 1)


if __name__ == '__main__':
    unittest.main()
