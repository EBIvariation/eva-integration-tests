import os
import shutil

from ebi_eva_common_pyutils.logger import logging_config as log_cfg
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query

from utils.test_with_docker_compose import TestWithDockerCompose

logger = log_cfg.get_logger(__name__)


class TestEvaSubmission(TestWithDockerCompose):
    vcf_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(TestWithDockerCompose.resources_directory, 'assembly_reports')

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_submission_test_run')
    metadata_xlsx = os.path.join(test_run_dir, 'metadata_xlsx.xlsx')
    old_metadata_xlsx = os.path.join(test_run_dir, 'old_metadata_xlsx.xlsx')
    metadata_json = os.path.join(test_run_dir, 'eva_sub_cli_metadata.json')

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-submission.yml')
    container_name = 'eva_submission_test'
    container_reference_genome_dir = '/opt/reference_sequences/nitrospira/GCA_000002945.2'
    container_submission_dir = '/opt/ftp/private/eva-box-01/upload/username'
    container_eload_dir = '/opt/submissions'

    maven_settings_file = os.path.join(TestWithDockerCompose.root_dir, 'components', 'maven-settings.xml')
    maven_profile = 'localhost'

    def setUp(self):
        super().setUp()
        self.container_log_files = []

    def assert_submission_processing_status_updated(self, submission_id, step, status):
        metadata_connection_handle = get_metadata_connection_handle(self.maven_profile, self.maven_settings_file)
        with metadata_connection_handle:
            submission_status_query = (f"SELECT status FROM eva_submissions.submission_processing_status "
                                       f"where submission_id = '{submission_id}' and step = '{step}'")
            results = get_all_results_for_query(metadata_connection_handle, submission_status_query)
            assert len(results) == 1
            assert results[0][0] == status
