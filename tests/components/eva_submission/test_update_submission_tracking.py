import os
import random
import shutil
from datetime import date, timedelta

import yaml
from ebi_eva_common_pyutils.config import Configuration
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query

from tests.components.eva_submission.test_eva_submission import TestEvaSubmission
from utils.docker_utils import read_file_from_container, copy_files_to_container, copy_files_from_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import log_on_failure


class TestEvaSubmissionUpdateSubmissionTracking(TestEvaSubmission):

    def setUp(self):
        self.webin_username = os.environ.get('EVA_SUBMISSION_WEBIN_USERNAME')
        self.webin_password = os.environ.get('EVA_SUBMISSION_WEBIN_PASSWORD')
        if not self.webin_username or not self.webin_password:
            self.fail('EVA_SUBMISSION_WEBIN_USERNAME or EVA_SUBMISSION_WEBIN_PASSWORD not set')

        super().setUp()

        # create metadata xlsx file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'EVA_Submission_v2.0_cpombe.xlsx'),
            self.metadata_xlsx
        )

        # The ELOAD number is used to generate the project alias which needs to be unique on ENA's side.
        # ENA's test server should delete the submissions every 24 hours
        # Probability that we use the same ELOAD number twice over 24 hours is low
        self.eload_number = random.randint(1, 1000000)

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    @log_on_failure
    def test_update_release_date(self):
        # Run preparation, validation, and brokering
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 --eload {self.eload_number}"
        )
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)
        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --eload {self.eload_number}'"
        )
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --eload {self.eload_number}'"
        )
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # Run update release date from command line
        log_file = f'{self.container_eload_dir}/ELOAD_{self.eload_number}/update_release_date.out'
        self.container_log_files.append((self.container_name, log_file))
        new_release_date = (date.today() + timedelta(weeks=48)).strftime('%Y-%m-%d')
        update_release_date_cmd = (
            f"docker exec {self.container_name} sh -c 'update_submission_tracking.py --eload_id {self.eload_number} --release_date {new_release_date} > {log_file} 2>&1'"
        )
        run_quiet_command("run eva_submission update_submission_tracking script", update_release_date_cmd)

        # Assert results
        copy_files_from_container(self.container_name, self.container_eload_dir, self.test_run_dir)
        eload_config_file = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}',
                                         f'.ELOAD_{self.eload_number}_config.yml')
        config = Configuration(eload_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None

        metadata_connection_handle = get_metadata_connection_handle(self.maven_profile, self.maven_settings_file)
        with metadata_connection_handle:
            submission_details_query = (f"SELECT release_date FROM eva_submissions.submission_tracking_details "
                                        f"where submission_id = '{submission_id}'")
            results = get_all_results_for_query(metadata_connection_handle, submission_details_query)
            assert len(results) == 1
            current_release_date = results[0][0]
            print(current_release_date)
            assert current_release_date is not None
            assert current_release_date == new_release_date

    def create_submission_dir_and_copy_files_to_container(self):
        # Get the config file from the container and update the username and password for Webin
        yaml_content = read_file_from_container(self.container_name,
                                                os.path.join('/root', '.submission_config.yml'))
        submission_config = yaml.safe_load(yaml_content)
        submission_config['biosamples'].update(
            {'webin_username': self.webin_username, 'webin_password': self.webin_password})
        submission_config['ena'].update({'username': self.webin_username, 'password': self.webin_password})

        tmp_yml = os.path.join(self.test_run_dir, '.submission_config.yml')
        with open(tmp_yml, 'w') as open_file:
            yaml.safe_dump(submission_config, open_file)
        copy_files_to_container(self.container_name, '/root', tmp_yml)
        os.remove(tmp_yml)

        # Prepare metadata spreadsheet
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

        # Prepare reference genome
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.assembly_reports_dir, 'GCA_000002945.2_assembly_report.txt'))
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.fasta_files_dir, 'GCA_000002945.2.fa'))

        vcf_file = os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
        copy_files_to_container(self.container_name, self.container_submission_dir, vcf_file)
