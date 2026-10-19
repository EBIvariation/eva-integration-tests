import json
import os

import yaml
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query

from tests.components.eva_sub_cli.test_eva_sub_cli import TestEvaSubCli
from utils.docker_utils import copy_files_to_container, read_file_from_container, run_docker_cmd, \
    run_command_in_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose, log_on_failure


class TestEvaSubCliToEvaSubmission(TestEvaSubCli):
    """eva-sub-cli uploads submission to mock-globus and eva-submission prepares it.

    mock-globus and eva-submission share a volume so that the files uploaded to mock-globus are found in the
    upload directory of the FTP used by eva-submission.
    """
    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_sub_cli_to_eva_submission_test_run')
    metadata_json = os.path.join(test_run_dir, 'metadata_json.json')

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-sub-cli-to-eva-submission.yml')

    # Two containers run the tested code: container_name (inherited from TestEvaSubCli) is the eva-sub-cli executor
    # and eva_submission_container_name is the eva-submission executor
    eva_submission_container_name = 'eva_submission_test'
    container_upload_dir = '/opt/ftp/private/eva-sub-cli/upload'
    container_eload_dir = '/opt/submissions'
    prepare_log_file = os.path.join(container_eload_dir, 'prepare.out')
    # Log files: the eva-sub-cli and eva-submission-ws logs from TestEvaSubCli,
    # plus the eva-submission prepare_submission log
    container_log_files = TestEvaSubCli.container_log_files + [(eva_submission_container_name, prepare_log_file)]

    eload_number = 1

    @log_on_failure
    def test_large_file_submitted_by_eva_sub_cli_is_prepared_by_eva_submission(self):
        # mock-globus rejects uploads larger than 1 MiB and eva-sub-cli uploads in parts of 512 KiB (UPLOAD_PART_SIZE set
        # in the docker compose file): this file is uploaded in 3 parts
        large_file_name = 'large_file.vcf.gz'
        large_file_size = 1024 * 1024 + 8 * 1024
        large_file = os.path.join(self.container_submission_dir, large_file_name)
        run_docker_cmd("create a large file in the container",
                       f"docker exec {self.container_name} sh -c 'head -c {large_file_size} /dev/urandom > {large_file}'")
        large_file_md5 = run_command_in_container(self.container_name, f'md5sum {large_file}').split()[0]

        sub_metadata = self.get_validation_json_metadata()
        sub_metadata['files'] = [{"analysisAlias": "AA", "fileName": large_file_name, "fileSize": large_file_size,
                                  "md5": large_file_md5}]
        sub_metadata['analysis'][0]['referenceGenome'] = 'GCA_000002945.2'
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)

        # Validation is considered passed for the large file
        config_file = os.path.join(self.test_run_dir, '.eva_sub_cli_config.yml')
        with open(config_file, 'w') as open_config:
            yaml.safe_dump({'metadata_json': os.path.join(self.container_submission_dir,
                                                          os.path.basename(self.metadata_json)),
                            'ready_for_submission_to_eva': True,
                            'vcf_files': [large_file]}, open_config)
        copy_files_to_container(self.container_name, self.container_submission_dir, config_file)

        # Submit with eva-sub-cli
        webin_account, webin_email, webin_password = self.webin_test_user.get_webin_submission_account_details()
        submission_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=NATIVE --tasks=SUBMIT "
            f"--submission_dir {self.container_submission_dir} "
            f"--metadata_json {os.path.join(self.container_submission_dir, os.path.basename(self.metadata_json))} "
            f"--username {webin_account} --password {webin_password}"
        )
        run_quiet_command("submit through eva-sub-cli", submission_cmd, log_error_stream_to_output=True)

        yaml_content = read_file_from_container(self.container_name,
                                                os.path.join(self.container_submission_dir, '.eva_sub_cli_config.yml'))
        submission_config = yaml.safe_load(yaml_content)
        # Check that the submission was successful
        assert submission_config['submission_complete'] is True
        # Collect the submission ID and Webin account
        submission_id = submission_config['submission_id']
        submission_account_id = f"{webin_account}_webin"

        # The parts uploaded to mock-globus are visible from eva-submission
        uploaded_files = run_command_in_container(
            self.eva_submission_container_name,
            f'ls {self.container_upload_dir}/{submission_account_id}/{submission_id}'
        ).split()
        assert sorted(uploaded_files) == sorted([f'{large_file_name}.part001', f'{large_file_name}.part002',
                                                 f'{large_file_name}.part003', 'metadata_json.json'])

        # Prepare the submission with eva-submission
        run_docker_cmd("Create submission directory in container",
                       f"docker exec {self.eva_submission_container_name} mkdir -p {self.container_eload_dir}")
        prepare_cmd = (
            f"docker exec {self.eva_submission_container_name} sh -c 'prepare_submission.py "
            f"--submission_id {submission_id} --eload {self.eload_number} > {self.prepare_log_file} 2>&1'"
        )
        run_quiet_command("run eva_submission prepare_submission script for a file uploaded in parts", prepare_cmd)
        # Prepare_submission also checks the uploaded file md5 against the one in the metadata json

        # The VCF file is assembled from its parts, and the parts are not copied
        vcf_dir = os.path.join(self.container_eload_dir, f'ELOAD_{self.eload_number}', '10_submitted', 'vcf_files')
        assert run_command_in_container(self.eva_submission_container_name, f'ls {vcf_dir}').split() == [large_file_name]

        eload_config = yaml.safe_load(read_file_from_container(
            self.eva_submission_container_name,
            os.path.join(self.container_eload_dir, f'ELOAD_{self.eload_number}', f'.ELOAD_{self.eload_number}_config.yml')
        ))
        assert eload_config['submission']['submission_id'] == submission_id

        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            query = (f"select submission_id, eload, source from eva_submissions.submission_eload "
                     f"where eload = {self.eload_number}")
            results = get_all_results_for_query(metadata_connection_handle, query)
            assert results == [(submission_id, self.eload_number, 'eva-sub-cli')]
