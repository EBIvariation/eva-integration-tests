import json
import os
import shutil
from unittest import TestCase

import requests
import yaml
from ebi_eva_internal_pyutils.config_utils import get_properties_from_xml_file
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query

from tests.webin.webin_test_user import WebinTestUser
from utils.docker_utils import copy_files_to_container, copy_files_from_container, build_from_docker_compose, \
    stop_and_remove_all_containers_in_docker_compose, start_all_containers_in_docker_compose, read_file_from_container
from utils.test_utils import run_quiet_command


class TestEvaSubCliValidation(TestCase):
    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    tests_directory = os.path.join(root_dir, 'tests')
    resources_directory = os.path.join(tests_directory, 'resources')

    vcf_files_dir = os.path.join(resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(resources_directory, 'assembly_reports')

    eva_sub_cli_test_run_dir = os.path.join(tests_directory, 'eva_sub_cli_test_run')
    metadata_json = os.path.join(eva_sub_cli_test_run_dir, 'metadata_json.json')
    metadata_xlsx = os.path.join(eva_sub_cli_test_run_dir, 'metadata_xlsx.xlsx')

    docker_compose_file = os.path.join(root_dir, 'components', 'docker-compose-eva-sub-cli.yml')
    container_name = 'eva_sub_cli_test'
    container_submission_dir = '/opt'

    webin_test_user = WebinTestUser()

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
        if os.path.exists(self.eva_sub_cli_test_run_dir):
            shutil.rmtree(self.eva_sub_cli_test_run_dir)
        os.makedirs(self.eva_sub_cli_test_run_dir, exist_ok=True)

        # create metadata json file
        sub_metadata = self.get_submission_json_metadata()
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        # create metadata xlsx file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_spreadsheets', 'EVA_Submission_Docker_Test.xlsx'),
            self.metadata_xlsx
        )

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    def tearDown(self):
        # delete test run directory
        if os.path.exists(self.eva_sub_cli_test_run_dir):
            shutil.rmtree(self.eva_sub_cli_test_run_dir)

        # stop and remove container
        stop_and_remove_all_containers_in_docker_compose(self.docker_compose_file)

    def test_native_validator_with_json(self):
        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=NATIVE --tasks=VALIDATE "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_json {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_json))} "
        )

        # Run validation from command line
        run_quiet_command("run eva_sub_cli native validator with json metadata using command line", validation_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_submission_dir, 'validation_output'),
                                  self.eva_sub_cli_test_run_dir)
        # assert results
        self.assert_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json(),
                                       'Validation passed successfully.', self.get_expected_semantic_val())

    def test_native_validator_with_xlsx(self):
        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=NATIVE --tasks=VALIDATE "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_xlsx {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_xlsx))} "
        )
        # Run validation from command line
        run_quiet_command("run eva_sub_cli native validator with xlsx metadata using command line",
                          validation_cmd, log_error_stream_to_output=True)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_submission_dir, 'validation_output'),
                                  self.eva_sub_cli_test_run_dir)
        # assert results
        self.assert_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json(),
                                       'Validation passed successfully.', self.get_expected_semantic_val())

    def test_native_validator_with_vcf_files(self):
        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=NATIVE --tasks=VALIDATE "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_json {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_json))} "
            f"--vcf_files {os.path.join(self.container_submission_dir, 'input_passed.vcf')} "
            f"--reference_fasta {os.path.join(self.container_submission_dir, 'input_passed.fa')} "
        )
        # Run validation from command line
        run_quiet_command("run eva_sub_cli native validator with vcf files and reference fasta using command line",
                          validation_cmd, log_error_stream_to_output=True)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_submission_dir, 'validation_output'),
                                  self.eva_sub_cli_test_run_dir)
        # assert results
        self.assert_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json(),
                                       'Validation passed successfully.', self.get_expected_semantic_val())

    def test_docker_validator_with_json(self):
        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=DOCKER --tasks=VALIDATE "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_json {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_json))} "
        )

        # Run validation from command line
        run_quiet_command("run eva_sub_cli docker validator with json metadata using command line",
                          validation_cmd, log_error_stream_to_output=True)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_submission_dir, 'validation_output'),
                                  self.eva_sub_cli_test_run_dir)
        # assert results
        self.assert_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json_docker(),
                                       'Validation passed successfully.', self.get_expected_semantic_val())

    def test_docker_validator_with_json_existing_project(self):
        # create metadata json file with existing project and copy to container
        sub_metadata = self.get_submission_json_metadata_existing_project()
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)

        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=DOCKER --tasks=VALIDATE "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_json {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_json))} "
        )

        # Run validation from command line
        run_quiet_command("run eva_sub_cli docker validator with json metadata using command line",
                          validation_cmd, log_error_stream_to_output=True)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_submission_dir, 'validation_output'),
                                  self.eva_sub_cli_test_run_dir)
        # assert results
        self.assert_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json_docker(),
                                       'Validation passed successfully.', self.get_expected_semantic_val())

    def test_docker_validator_with_xlsx(self):
        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=DOCKER --tasks=VALIDATE "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_xlsx {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_xlsx))} "
        )
        # Run validation from command line
        run_quiet_command("run eva_sub_cli docker validator with xlsx metadata using command line",
                          validation_cmd, log_error_stream_to_output=True)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_submission_dir, 'validation_output'),
                                  self.eva_sub_cli_test_run_dir)
        # assert results
        self.assert_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json_docker(),
                                       'Validation passed successfully.', self.get_expected_semantic_val())

    def test_eva_sub_cli_submission(self):
        # copy validation success config file for the test submission
        validation_passed_config_file = os.path.join(self.resources_directory, 'validation_passed_config_file',
                                                     '.eva_sub_cli_config.yml')
        copy_files_to_container(self.container_name, self.container_submission_dir,
                                validation_passed_config_file)

        webin_submission_account, webin_user_email, webin_user_password = self.webin_test_user.get_webin_submission_account_details()

        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=NATIVE --tasks=SUBMIT "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_json {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_json))} "
            f"--username {webin_submission_account} --password {webin_user_password}"
        )
        # Run validation from command line
        run_quiet_command("submit through eva-sub-cli", validation_cmd,
                          log_error_stream_to_output=True)

        # assert submission result
        self.assert_submission_results(webin_submission_account, webin_user_email)

    def test_eva_sub_cli_submission_existing_project(self):
        # create metadata json file with existing project and copy to container
        sub_metadata = self.get_submission_json_metadata_existing_project()
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)

        # copy validation success config file for the test submission
        validation_passed_config_file = os.path.join(self.resources_directory, 'validation_passed_config_file',
                                                     '.eva_sub_cli_config.yml')
        copy_files_to_container(self.container_name, self.container_submission_dir,
                                validation_passed_config_file)

        webin_submission_account, webin_user_email, webin_user_password = self.webin_test_user.get_webin_submission_account_details()

        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=NATIVE --tasks=SUBMIT "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_json {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_json))} "
            f"--username {webin_submission_account} --password {webin_user_password}"
        )
        # Run validation from command line
        run_quiet_command("submit through eva-sub-cli", validation_cmd,
                          log_error_stream_to_output=True)

        # assert submission result
        self.assert_submission_results(webin_submission_account, webin_user_email, existing_project=True)

    def create_submission_dir_and_copy_files_to_container(self):
        for directory in [self.vcf_files_dir, self.fasta_files_dir, self.assembly_reports_dir]:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                copy_files_to_container(self.container_name, self.container_submission_dir, file_path)

        if self.metadata_json:
            copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)
        if self.metadata_xlsx:
            copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

    def get_submission_json_metadata_existing_project(self):
        json_metadata = self.get_submission_json_metadata()
        json_metadata['project'] = {'projectAccession': 'PRJEB12770'}
        return json_metadata

    def get_submission_json_metadata(self):
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
                    "fileName": "input_passed.vcf",
                    "fileSize": 45050,
                    "fileType": "vcf"
                }
            ]
        }

    def get_expected_metadata_files_json(self):
        return [
            '96a80c9368cc3c37095c86fbe6044fb2 45050 /opt/input_passed.vcf'
        ]

    def get_expected_metadata_files_json_docker(self):
        return [
            '96a80c9368cc3c37095c86fbe6044fb2 45050 /opt/vcf_validation/opt/input_passed.vcf'
        ]

    def get_expected_semantic_val(self):
        return {'description': 'SAME123 does not exist or is private',
                'property': '/sample/0/bioSampleAccession'}

    def get_expected_sample(self):
        return {
            'overall_differences': False,
            'results_per_analysis': {
                'AA': {
                    'difference': False,
                    'more_metadata_submitted_files': [],
                    'more_per_submitted_files_metadata': {},
                    'more_submitted_files_metadata': []
                }
            }
        }

    def assert_validation_results(self, expected_sample_checker, expected_metadata_files_json,
                                  expected_metadata_val, expected_semantic_val):
        validation_output_dir = self.eva_sub_cli_test_run_dir

        vcf_format_dir = os.path.join(validation_output_dir, 'vcf_format')
        self.assertTrue(os.path.exists(vcf_format_dir))

        vcf_format_log_file = os.path.join(vcf_format_dir, 'input_passed.vcf.vcf_format.log')
        self.assertTrue(os.path.exists(vcf_format_log_file))

        with open(vcf_format_log_file) as vcf_format_log_file:
            vcf_format_logs = vcf_format_log_file.readlines()
            self.assertEqual('[info] According to the VCF specification, the input file is valid\n',
                             vcf_format_logs[2])
            text_report = vcf_format_logs[1].split(':')[1].strip()
            with open(os.path.join(validation_output_dir, text_report)) as text_report:
                text_report_content = text_report.readlines()
                self.assertEqual('According to the VCF specification, the input file is valid\n',
                                 text_report_content[0])

        # assert assembly report
        assembly_check_dir = os.path.join(validation_output_dir, 'assembly_check')
        self.assertTrue(os.path.exists(assembly_check_dir))

        assembly_check_log_file = os.path.join(assembly_check_dir, 'input_passed.vcf.assembly_check.log')
        self.assertTrue(os.path.exists(assembly_check_log_file))

        with open(assembly_check_log_file) as assembly_check_log_file:
            assembly_check_logs = assembly_check_log_file.readlines()
            self.assertEqual('[info] Number of matches: 247/247\n', assembly_check_logs[4])
            self.assertEqual('[info] Percentage of matches: 100%\n', assembly_check_logs[5])

        # Assert Samples concordance
        self.assert_sample_checker(os.path.join(validation_output_dir, 'other_validations', 'sample_checker.yml'),
                                   expected_sample_checker)

        with open(os.path.join(validation_output_dir, 'other_validations', 'file_info.txt')) as open_file:
            file_info_lines = [line.strip() for line in open_file.readlines()]
            assert len(file_info_lines) == len(expected_metadata_files_json)

            for actual_line, expected_line in zip(file_info_lines, expected_metadata_files_json):
                assert actual_line == expected_line

        # Check metadata errors
        with open(os.path.join(validation_output_dir, 'other_validations', 'metadata_validation.txt')) as open_file:
            metadata_val_lines = {l.strip() for l in open_file.readlines()}
            assert any((expected_metadata_val in line for line in metadata_val_lines))

        # Check semantic metadata errors
        semantic_yaml_file = os.path.join(validation_output_dir, 'other_validations', 'metadata_semantic_check.yml')
        self.assertTrue(os.path.isfile(semantic_yaml_file))
        with open(semantic_yaml_file) as open_yaml:
            semantic_output = yaml.safe_load(open_yaml)
            assert semantic_output[0] == expected_semantic_val

    def assert_submission_results(self, webin_submission_account, webin_user_email, existing_project=False):
        # assert submission config file
        yaml_content = read_file_from_container(self.container_name,
                                                os.path.join('/opt', '.eva_sub_cli_config.yml'))
        submission_config_file = yaml.safe_load(yaml_content)
        assert submission_config_file['submission_complete'] is True
        assert 'submission_id' in submission_config_file
        assert 'submission_upload_url' in submission_config_file

        submission_id = submission_config_file['submission_id']
        submission_account_id = f"{webin_submission_account}_webin"
        settings_file = os.path.join(self.resources_directory, 'maven-settings.xml')

        # assert db details
        with get_metadata_connection_handle('docker', settings_file) as metadata_connection_handle:
            # assert submission account details
            submission_account_query = f"SELECT id, user_id FROM eva_submissions.submission_account WHERE id='{submission_account_id}'"
            for id, user_id in get_all_results_for_query(metadata_connection_handle, submission_account_query):
                assert id == submission_account_id
                assert user_id == webin_submission_account

            # assert submission details
            submission_query = (f"SELECT submission_id,  status, submission_account_id "
                                f"FROM eva_submissions.submission WHERE submission_id='{submission_id}'")
            for id, status, submission_account in get_all_results_for_query(metadata_connection_handle,
                                                                            submission_query):
                assert id == submission_id
                assert status == 'UPLOADED'
                assert submission_account == submission_account_id

        # assert details from webservice

        # assert submission status
        response = requests.get(
            f'http://localhost:8080/eva/webservices/submission-ws/v1/submission/{submission_id}/status')
        assert response.text == 'UPLOADED'

        # assert submission details
        profile_properties = get_properties_from_xml_file('docker', settings_file)
        response = requests.get(
            f'http://localhost:8080/eva/webservices/submission-ws/v1/admin/submission/{submission_id}',
            auth=(profile_properties['submission-ws.admin-user'], profile_properties['submission-ws.admin-password']))
        response_data = response.json()
        if existing_project:
            assert response_data['submissionId'] == submission_id
            assert response_data['metadataJson']['files'][0] == {'analysisAlias': 'AA', 'fileName': 'input_passed.vcf',
                                                                 'fileSize': 45050, 'fileType': 'vcf'}
            assert response_data['metadataJson']['submitterDetails'][0] == {'centre': 'test_user_centre',
                                                                            'email': 'test_user_email@abc.com',
                                                                            'firstName': 'test_user_first_name',
                                                                            'laboratory': 'test_user_laboratory',
                                                                            'lastName': 'test_user_last_name'}
        else:
            assert response_data['submissionId'] == submission_id
            assert response_data['projectTitle'] == 'test_project_title'
            assert response_data['projectDescription'] == 'test_project_description'
            assert response_data['metadataJson']['project'] == {'centre': 'test_project_centre',
                                                                'description': 'test_project_description',
                                                                'taxId': 1234,
                                                                'title': 'test_project_title'}
            assert response_data['metadataJson']['files'][0] == {'analysisAlias': 'AA', 'fileName': 'input_passed.vcf',
                                                                 'fileSize': 45050, 'fileType': 'vcf'}
            assert response_data['metadataJson']['submitterDetails'][0] == {'centre': 'test_user_centre',
                                                                            'email': 'test_user_email@abc.com',
                                                                            'firstName': 'test_user_first_name',
                                                                            'laboratory': 'test_user_laboratory',
                                                                            'lastName': 'test_user_last_name'}

        # assert emails sent for submission upload
        mailhog_email_mgs_url = get_properties_from_xml_file("docker", settings_file)['mailhog.email-messages']
        response = requests.get(mailhog_email_mgs_url)
        emails = response.json()

        # assert email sent to eva-helpdesk on submission upload
        eva_helpdesk_email = get_properties_from_xml_file('docker', settings_file)['eva.helpdesk-email']
        mail_to_helpdesk = [email for email in emails
                            if eva_helpdesk_email in email['Content']['Headers'].get('To', [])
                            and 'eva-noreply@ebi.ac.uk' in email['Content']['Headers'].get('From', [])
                            and f"New Submission Uploaded. Submission Id - ({submission_id})"
                            in email['Content']['Headers'].get('Subject', [])
                            ]
        assert len(mail_to_helpdesk) == 1

        # assert email sent to user on submission upload
        mail_to_user = [email for email in emails
                        if webin_user_email in email['Content']['Headers'].get('To', [])
                        and 'eva-helpdesk@ebi.ac.uk' in email['Content']['Headers'].get('From', [])
                        and f"EVA Submission Update: UPLOADED SUCCESS" in email['Content']['Headers'].get('Subject', [])
                        and f"Here is the update for your submission: <br /><br />Submission ID: {submission_id}<br />"
                        in email['Content']['Body']
                        ]
        assert len(mail_to_user) == 1

    def assert_same_dict_and_unordered_list(self, o1, o2):
        if isinstance(o1, dict) and isinstance(o2, dict):
            self.assertEqual(set(o1), set(o2))
            [self.assert_same_dict_and_unordered_list(o1.get(k), o2.get(k)) for k in o1]
        elif isinstance(o1, list) and isinstance(o2, list):
            self.assertEqual(set(o1), set(o2))
        else:
            self.assertEqual(o1, o2)

    def assert_sample_checker(self, sample_checker_file, expected_checker):
        self.assertTrue(os.path.isfile(sample_checker_file))
        with open(sample_checker_file) as open_yaml:
            self.assert_same_dict_and_unordered_list(yaml.safe_load(open_yaml), expected_checker)
