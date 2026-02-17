import os

from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query
from ebi_eva_common_pyutils.logger import logging_config as log_cfg

from tests.webin.webin_test_user import WebinTestUser
from utils.docker_utils import copy_files_to_container
from utils.test_with_docker_compose import TestWithDockerCompose

logger = log_cfg.get_logger(__name__)

class TestEvaSubCli(TestWithDockerCompose):
    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    tests_directory = os.path.join(root_dir, 'tests')
    resources_directory = os.path.join(tests_directory, 'resources')

    vcf_files_dir = os.path.join(resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(resources_directory, 'assembly_reports')

    test_run_dir = os.path.join(tests_directory, 'eva_sub_cli_test_run')
    metadata_json = os.path.join(test_run_dir, 'metadata_json.json')
    metadata_xlsx = os.path.join(test_run_dir, 'metadata_xlsx.xlsx')

    docker_compose_file = os.path.join(root_dir, 'components', 'docker-compose-eva-sub-cli.yml')
    container_name = 'eva_sub_cli_test'
    container_submission_dir = '/opt'
    log_file = os.path.join(container_submission_dir, 'eva_submission.log')

    webin_test_user = WebinTestUser()

    def setUp(self):
        super().setUp()
        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    def create_submission_dir_and_copy_files_to_container(self):
        for directory in [self.vcf_files_dir, self.fasta_files_dir, self.assembly_reports_dir]:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                copy_files_to_container(self.container_name, self.container_submission_dir, file_path)

    def get_validation_json_metadata_existing_project(self):
        json_metadata = self.get_validation_json_metadata()
        json_metadata['project'] = {'projectAccession': 'PRJEB12770'}
        return json_metadata

    def get_validation_json_metadata_with_non_vcf_file(self):
        json_metadata = self.get_validation_json_metadata()
        json_metadata['files'].append({
            "analysisAlias": "AA",
            "fileName": "input_passed.vcf.gz.tbi"
        })
        return json_metadata

    def get_validation_json_metadata_without_files(self):
        json_metadata = self.get_validation_json_metadata()
        json_metadata['files'] = []
        return json_metadata

    def get_validation_json_metadata_multiple_analysis_without_files(self):
        json_metadata = self.get_validation_json_metadata()
        json_metadata['analysis'].append({
                    "analysisTitle": "another_analysis_title",
                    "analysisAlias": "BB",
                    "description": "another_analysis_description",
                    "experimentType": "Whole genome sequencing",
                    "referenceGenome": "test_analysis_reference_genome",
                    "referenceFasta": "input_passed.fa",
                    "assemblyReport": "input_passed.txt"
                })
        json_metadata['sample'].append({
                    "analysisAlias": ["BB"],
                    "sampleInVCF": "HG00097",
                    "bioSampleAccession": "SAME456"
                })
        json_metadata['files'] = []
        return json_metadata

    def get_validation_json_metadata(self):
        return {
            "submitterDetails": [
                {
                    "firstName": "test_user_first_name",
                    "lastName": "test_user_last_name",
                    "email": "test_user_email@abc.com",
                    "laboratory": "test_user_laboratory",
                    "centre": "test_user_centre"
                }
            ],
            "project": {
                "title": "test_project_title",
                "description": "test_project_description",
                "taxId": 1234,
                "centre": "test_project_centre"
            },
            "analysis": [
                {
                    "analysisTitle": "test_analysis_title",
                    "analysisAlias": "AA",
                    "description": "test_analysis_description",
                    "experimentType": "Whole genome sequencing",
                    "referenceGenome": "test_analysis_reference_genome",
                    "referenceFasta": "input_passed.fa",
                    "assemblyReport": "input_passed.txt"
                }
            ],
            "sample": [
                {
                    "analysisAlias": ["AA"],
                    "sampleInVCF": "HG00096",
                    "bioSampleAccession": "SAME123"
                }
            ],
            "files": [
                {
                    "analysisAlias": "AA",
                    "fileName": "input_passed.vcf"
                }
            ]
        }

    def assert_call_home_events_exist(self, expected_events=None, expected_tasks_list=None, expected_executors=None, metadata_connection_handle=None):
        if not metadata_connection_handle:
            settings_file = os.path.join(self.resources_directory, 'maven-settings.xml')
            metadata_connection_handle = get_metadata_connection_handle('docker', settings_file)
        with metadata_connection_handle:
            call_home_query = (f"SELECT event_type, tasks, executor, raw_payload FROM eva_submissions.call_home_event")
            results = get_all_results_for_query(metadata_connection_handle, call_home_query)
            event_types = []
            tasks_list = []
            raw_payloads = []
            executors = []
            for call_home_event in results:
                event_type, tasks, executor, raw_payload = call_home_event
                logger.warning(f'event_type={event_type}')
                logger.warning(f'tasks={tasks}')
                logger.warning(f'executors={executors}')
                logger.warning(f'raw_payload={raw_payload}')
                # id, deployment_id, run_id, event_type, cli_version, created_at, runtime_seconds, executor, tasks, raw_payload = call_home_event
                event_types.append(event_type)
                tasks_list.append(tasks)
                executors.append(executor)
                raw_payloads.append(raw_payload)
            assert len(results) > 0
            if expected_events is not None:
                assert event_types == expected_events
            if expected_tasks_list is not None:
                assert tasks_list == expected_tasks_list
            if expected_executors is not None:
                assert executors == expected_executors
            return raw_payloads