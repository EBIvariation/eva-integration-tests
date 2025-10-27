import os
import shutil
from unittest import TestCase

from utils.docker_utils import build_from_docker_compose, \
    stop_and_remove_all_containers_in_docker_compose, start_all_containers_in_docker_compose, read_file_from_container


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
    log_file = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # build and setup images/containers present in the docker compose file
        build_from_docker_compose(cls.docker_compose_file)

    def setUp(self):
        # stop and remove containers
        stop_and_remove_all_containers_in_docker_compose(self.docker_compose_file)
        # start containers
        start_all_containers_in_docker_compose(self.docker_compose_file)

        # delete and recreate the test run dir
        if os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir)
        os.makedirs(self.test_run_dir, exist_ok=True)

    def tearDown(self):
        # Show the log file to get a better description of what happened
        if self.log_file:
            try:
                output = read_file_from_container(self.container_name, self.log_file)
                print('Log file:')
                print(output)
            except Exception as e:
                print(f'Failed to read log {self.log_file} file from {self.container_name}')
                print(str(e))

        # delete test run directory
        if os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir)

        # stop and remove container
        stop_and_remove_all_containers_in_docker_compose(self.docker_compose_file)
