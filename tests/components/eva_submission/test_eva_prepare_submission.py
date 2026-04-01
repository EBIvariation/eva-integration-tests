import json
import os

from ebi_eva_common_pyutils.config import Configuration
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import execute_query, get_all_results_for_query

from utils.docker_utils import copy_files_to_container, run_docker_cmd, copy_files_from_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose, log_on_failure


class TestEvaSubmissionPreparation(TestWithDockerCompose):
    maven_settings_file = os.path.join(TestWithDockerCompose.root_dir, 'components', 'maven-settings.xml')
    maven_profile = 'localhost'
    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_submission_test_run')

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-submission.yml')
    container_name = 'eva_submission_test'

    submission_account_id = "test_submission_account"
    submission_id = "test_submission_id"
    container_submission_dir = '/opt/ftp/private/eva-box-01/upload/username'
    container_submission_dir_json_webservice = f'/opt/ftp/private/eva-sub-cli/upload/{submission_account_id}/{submission_id}'
    container_eload_dir = '/opt/submissions'

    def setUp(self):
        super().setUp()
        self.container_log_files = []
        self.eload_number = 1

    @log_on_failure
    def test_prepare_submission_metadata_spreadsheet(self):
        # copy all required file into container
        self.setup_test_data_for_metadata_spreadsheet()

        log_file = f'{self.container_eload_dir}/prepare.out'
        self.container_log_files.append((self.container_name, log_file))
        # Run preparation from command line
        prepare_cmd = (
            f"docker exec {self.container_name} sh -c 'prepare_submission.py --submitter username --ftp_box 1 --eload {self.eload_number} > {log_file} 2>&1'"
        )
        run_quiet_command("run eva_submission prepare_submission script for metadata spreadsheet", prepare_cmd)

        # assert submission id written to eload config and present in DB
        copy_files_from_container(self.container_name, os.path.join(self.container_eload_dir), self.test_run_dir)
        eload_config_yml = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}',
                                        f'.ELOAD_{self.eload_number}_config.yml')
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)
        assert config['submission']['submission_id'] is not None
        submission_id = config['submission']['submission_id']

        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            query = (
                f"select submission_id, eload, source from eva_submissions.submission_eload where eload = {self.eload_number}")
            results = get_all_results_for_query(metadata_connection_handle, query)
            assert len(results) == 1
            assert results[0][0] == submission_id
            assert results[0][1] == self.eload_number
            assert results[0][2] == "email"

            query = (f"select submission_id from eva_submissions.submission where submission_id = '{submission_id}'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            assert len(results) == 1
            assert results[0][0] == submission_id

    @log_on_failure
    def test_prepare_submission_metadata_json_from_webservice(self):
        # copy all required file into container
        self.setup_test_data_for_metadata_json_from_webservice()

        log_file = f'{self.container_eload_dir}/prepare.out'
        self.container_log_files.append((self.container_name, log_file))
        # Run preparation from command line
        prepare_cmd = (
            f"docker exec {self.container_name} sh -c 'prepare_submission.py --submission_id {self.submission_id} --eload {self.eload_number} > {log_file} 2>&1'"
        )
        run_quiet_command("run eva_submission prepare_submission script for metadata json from webservice", prepare_cmd)

        # assert submission id written to eload config
        copy_files_from_container(self.container_name, os.path.join(self.container_eload_dir), self.test_run_dir)
        eload_config_yml = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}',
                                        f'.ELOAD_{self.eload_number}_config.yml')
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)
        assert config['submission']['submission_id'] == self.submission_id

        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            query = (
                f"select submission_id, eload, source from eva_submissions.submission_eload where eload = {self.eload_number}")
            results = get_all_results_for_query(metadata_connection_handle, query)
            assert len(results) == 1
            assert results[0][0] == self.submission_id
            assert results[0][1] == self.eload_number
            assert results[0][2] == "eva-sub-cli"

    def setup_test_data_for_metadata_spreadsheet(self):
        vcf_file = os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
        run_docker_cmd(f"Create submission directory in container",
                       f"docker exec {self.container_name} mkdir -p {self.container_eload_dir}")
        copy_files_to_container(self.container_name, self.container_submission_dir, vcf_file)
        copy_files_to_container(self.container_name, self.container_submission_dir,
                                os.path.join(self.resources_directory, 'metadata_files',
                                             'EVA_Submission_v2.0_cpombe.xlsx'))

    def setup_test_data_for_metadata_json_from_webservice(self):
        # copy vcf file to the correct dir in container
        vcf_file = os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
        run_docker_cmd(f"Create submission directory in container",
                       f"docker exec {self.container_name} mkdir -p {self.container_eload_dir}")
        copy_files_to_container(self.container_name, self.container_submission_dir_json_webservice, vcf_file)

        # insert data in eva-submission-ws tables
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            # insert submission account
            submission_account_query = (
                f"INSERT INTO eva_submissions.submission_account (id, first_name, last_name, login_type, primary_email, user_id) "
                f"VALUES('{self.submission_account_id}', 'Test', 'User', 'webin', 'test-user@email.com', '{self.submission_account_id}')")
            execute_query(metadata_connection_handle, submission_account_query)

            # insert submission
            submission_query = (
                f"INSERT INTO eva_submissions.submission (submission_id, completion_time, initiation_time, status, upload_url, uploaded_time, submission_account_id) "
                f"VALUES('{self.submission_id}', NULL, '2025-05-21 18:43:25.384', 'UPLOADED', 'test-upload-url', '2025-05-21 19:10:30.232', '{self.submission_account_id}')")
            execute_query(metadata_connection_handle, submission_query)

            # insert submission_details
            metadata_json = json.dumps(self.get_metadata_json_data_for_submission_details())
            submission_details_query = (
                f"INSERT INTO eva_submissions.submission_details (submission_id, metadata_json, project_description, project_title) "
                f"VALUES('{self.submission_id}', '{metadata_json}', 'test-project-description', 'test-project-title')")
            execute_query(metadata_connection_handle, submission_details_query)

    def get_metadata_json_data_for_submission_details(self):
        return {
            "submitterDetails": [
                {
                    "lastName": "test_user_last_name",
                    "firstName": "test_user_first_name",
                    "email": "test_user_email@abc.com",
                    "laboratory": "test_user_laboratory",
                    "centre": "test_user_centre"
                }
            ],
            "project": {
                "title": "test_project",
                "description": "test_project_description",
                "taxId": 1234,
                "centre": "test_project_centre"
            },
            "sample": [
                {
                    "analysisAlias": ["AA"],
                    "sampleInVCF": "S1",
                    "bioSampleObject": {
                        "name": "S1",
                        "characteristics": {
                            "title": [
                                {
                                    "text": "The Schizosaccharomyces pombe  sample"
                                }
                            ],
                            "description": [
                                {
                                    "text": "Test Description"
                                }
                            ],
                            "taxId": [
                                {
                                    "text": "4896"
                                }
                            ],
                            "scientificName": [
                                {
                                    "text": "Schizosaccharomyces pombe"
                                }
                            ],
                            "sex": [
                                {
                                    "text": "Female"
                                }
                            ],
                            "tissueType": [
                                {
                                    "text": "skin"
                                }
                            ],
                            "species": [
                                {
                                    "text": "Schizosaccharomyces pombe"
                                }
                            ]
                        }
                    }
                }
            ],
            "analysis": [
                {
                    "analysisTitle": "test_analysis_title",
                    "analysisAlias": "AA",
                    "description": "test_analysis_description",
                    "experimentType": "Whole genome sequencing",
                    "referenceGenome": "GCA_000002945.2"
                }
            ],
            "files": [
                {
                    "analysisAlias": "AA",
                    "fileName": "vcf_file_ASM294v2.vcf",
                    "fileType": "vcf"
                }
            ]
        }