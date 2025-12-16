import json
import os

import requests
import yaml
from ebi_eva_internal_pyutils.config_utils import get_properties_from_xml_file
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query

from tests.components.eva_sub_cli.test_eva_sub_cli import TestEvaSubCli
from utils.docker_utils import copy_files_to_container, read_file_from_container
from utils.test_utils import run_quiet_command


class TestEvaSubCliSubmission(TestEvaSubCli):

    def test_submission(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_submission_json_metadata()
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
        self.assert_submission_results(webin_submission_account, webin_user_email)

    def test_submission_to_existing_project(self):
        # create metadata json file and copy to container
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

    def get_submission_json_metadata(self):
        json_metadata = self.get_validation_json_metadata()
        json_metadata['files'] = [
            {
                "analysisAlias": "AA",
                "fileName": "input_passed.vcf",
                "fileSize": 45050
            }
        ]
        return json_metadata

    def get_submission_json_metadata_existing_project(self):
        json_metadata = self.get_validation_json_metadata_existing_project()
        json_metadata['files'] = [
            {
                "analysisAlias": "AA",
                "fileName": "input_passed.vcf",
                "fileSize": 45050
            }
        ]
        return json_metadata

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
                                                                 'fileSize': 45050}
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
                                                                 'fileSize': 45050}
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
