import functools
import os
import shutil
from unittest import TestCase

from utils.docker_utils import build_from_docker_compose, \
    stop_and_remove_all_containers_in_docker_compose, start_all_containers_in_docker_compose, read_file_from_container


def _dump_logs(test_instance):
    if test_instance.container_log_files:
        for container_name, log_file in test_instance.container_log_files:
            try:
                output = read_file_from_container(container_name, log_file)
                print('Log file: ' + log_file)
                print(output)
            except Exception as e:
                print(f'Failed to read log {log_file} file from {container_name}')
                print(str(e))


class log_on_failure:
    """Print container log files when an exception is raised.

    As a class-level decorator (test instance extracted from first arg at call time):
        @log_on_failure
        def assert_something(self, ...):
            ...

    As a context manager inside a test:
        with log_on_failure(self):
            ...

    """

    def __init__(self, test_instance_or_func):
        """Detect usage mode from the argument type.

        When given a callable (function/method), enters decorator mode: the instance wraps that
        function and will dump logs if it raises. functools.update_wrapper copies __name__ and
        related attributes so test runners can still discover test_* methods by name.

        When given a TestWithDockerCompose instance, enters context manager mode: __enter__ /
        __exit__ will dump logs if the block raises.
        """
        if callable(test_instance_or_func) and not isinstance(test_instance_or_func, TestWithDockerCompose):
            # @log_on_failure — receives the function to wrap
            self._func = test_instance_or_func
            self._test_instance = None
            functools.update_wrapper(self, test_instance_or_func)
        elif isinstance(test_instance_or_func, TestWithDockerCompose):
            # with log_on_failure(self) — receives the TestWithDockerCompose instance
            self._func = None
            self._test_instance = test_instance_or_func
        else:
            raise TypeError('Must be use as a decorator around test function of a TestWithDockerCompose or '
                            'as context manager receiving a TestWithDockerCompose instance')

    def __get__(self, obj, objtype=None):
        """Descriptor protocol: bind the test instance so it is passed as the first argument.

        Without this, accessing self.decorated_method on a TestWithDockerCompose instance would
        return the bare log_on_failure object (not bound to anything), so __call__ would receive
        the method's own arguments without the test instance prepended. __get__ returns a partial
        that pre-fills obj, replicating the behaviour of regular bound methods.
        """
        if obj is None:
            return self
        return functools.partial(self, obj)

    def __call__(self, *args, **kwargs):
        """Execute the wrapped function or finalise decorator-factory usage.

        In decorator mode (_func is set): called by the test runner with the test instance as
        args[0]. Runs the wrapped function and dumps logs if it raises.

        In context-manager / decorator-factory mode (_func is None): called with the function to
        wrap (i.e. @log_on_failure(self) syntax). Returns a wrapper that dumps logs on failure.
        """
        if self._func is not None:
            test_self = args[0]
            try:
                return self._func(*args, **kwargs)
            except Exception:
                _dump_logs(test_self)
                raise
        func = args[0]
        test_instance = self._test_instance
        def wrapper(*w_args, **w_kwargs):
            try:
                return func(*w_args, **w_kwargs)
            except Exception:
                _dump_logs(test_instance)
                raise
        return wrapper

    def __enter__(self):
        """Enter the context manager block; no setup needed."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """On exception, dump container logs before letting the exception propagate."""
        if exc_type is not None:
            _dump_logs(self._test_instance)
        return False


class TestWithDockerCompose(TestCase):
    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
    tests_directory = os.path.join(root_dir, 'tests')
    resources_directory = os.path.join(tests_directory, 'resources')

    vcf_files_dir = os.path.join(resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(resources_directory, 'assembly_reports')

    test_run_dir = None
    docker_compose_file = None
    container_name = None
    container_submission_dir = None
    container_log_files = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # build and setup images/containers present in the docker compose file
        build_from_docker_compose(cls.docker_compose_file)

    def setUp(self):
        # stop and remove containers
        stop_and_remove_all_containers_in_docker_compose(self.docker_compose_file)

        # delete and recreate the test run dir before starting containers so that
        # bind mounts point to a host directory with correct permissions
        if self.test_run_dir:
            if os.path.exists(self.test_run_dir):
                shutil.rmtree(self.test_run_dir, ignore_errors=True)
            os.makedirs(self.test_run_dir, exist_ok=True)

        # start containers
        start_all_containers_in_docker_compose(self.docker_compose_file)

    def tearDown(self):
        # delete test run directory
        if self.test_run_dir and os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir, ignore_errors=True)

        # stop and remove container
        stop_and_remove_all_containers_in_docker_compose(self.docker_compose_file)
