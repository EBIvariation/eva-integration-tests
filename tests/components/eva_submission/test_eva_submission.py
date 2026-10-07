import os
import re
import shutil

from ebi_eva_common_pyutils.logger import logging_config as log_cfg
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query, execute_query

from utils.test_with_docker_compose import TestWithDockerCompose

logger = log_cfg.get_logger(__name__)


def extract_nextflow_work_dirs_from_log(input_file):
    """
    Extract the value following 'work-dir' from a log line containing the nextflow command.
    """
    pattern = re.compile(r"work-dir\s+(\S+)")

    with open(input_file, "r") as f:
        for line in f:
            if "Running command:" in line and "nextflow" in line:
                match = pattern.search(line)
                if match:
                    yield match.group(1)

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
    container_ftp_submission_dir = '/opt/ftp/private/eva-box-01/upload/username'
    container_submission_dir = '/opt/submissions'

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

    def get_submission_id_from_db(self, eload_number):
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            query = (
                f"select submission_id, eload, source from eva_submissions.submission_eload where eload = {eload_number}")
            results = get_all_results_for_query(metadata_connection_handle, query)
            return results[0][0]

    def put_submission_in_db(self, submission_id, eload_number, source_type="email"):
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            query = (
                f"INSERT INTO eva_submissions.submission_account(id, user_id, login_type, primary_email, first_name, last_name) "
                f"VALUES('Webin-9999_webin', 'Webin-9999', 'webin', 'user@example.com', 'user', 'user')")
            execute_query(metadata_connection_handle, query)

            query = (
                f" INSERT INTO eva_submissions.submission(submission_id, status, submission_account_id, initiation_time) "
                f"VALUES('{submission_id}', 'OPEN', 'Webin-9999_webin', now())")
            execute_query(metadata_connection_handle, query)

            query = (
                f"INSERT INTO eva_submissions.submission_details(submission_id, project_title, project_description, metadata_json) "
                f"VALUES('{submission_id}', 'Test Project', 'Test Description', '{{}}'::jsonb)")
            execute_query(metadata_connection_handle, query)

            query = (f"insert into eva_submissions.submission_eload (submission_id, eload, source) "
                     f"values ('{submission_id}', {eload_number}, '{source_type}')")
            execute_query(metadata_connection_handle, query)



