import os
import shutil

import yaml
from ebi_eva_common_pyutils.config import Configuration

from utils.docker_utils import copy_files_to_container, copy_files_from_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose


class TestEvaSubmissionValidation(TestWithDockerCompose):

    vcf_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(TestWithDockerCompose.resources_directory, 'assembly_reports')

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_submission_test_run')
    metadata_xlsx = os.path.join(test_run_dir, 'metadata_xlsx.xlsx')

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components', 'docker-compose-eva-submission.yml')
    container_name = 'eva_submission_test'
    container_submission_dir = '/opt/ftp/private/eva-box-01/upload/username'
    container_eload_dir = '/opt/submissions'

    def setUp(self):
        super().setUp()
        # create metadata xlsx file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_spreadsheets', 'EVA_Submission_v2.0_cpombe.xlsx'),
            self.metadata_xlsx
        )

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    def test_submission_with_new_metadata_spreadsheet(self):
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 --eload 1"
        )

        # Run preparation from command line
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --eload 1 > {self.container_eload_dir}/ELOAD_1/validation.out'"
        )
        # Run validation from command line
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_eload_dir),
                                  self.test_run_dir)
        # assert results
        self.assert_validation_pass_in_config(os.path.join(self.test_run_dir, 'ELOAD_1','.ELOAD_1_config.yml'))


    def create_submission_dir_and_copy_files_to_container(self):
        vcf_file = os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
        copy_files_to_container(self.container_name, self.container_submission_dir, vcf_file)
        if self.metadata_xlsx:
            copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)


    def assert_validation_pass_in_config(self, eload_config_yml):
        # Check that the config file exists
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)
        # Check that each validation does pass
        for check in ['vcf_check', 'assembly_check', 'metadata_check', 'sample_check']:
            print(check)
            print(config.query('validation'))
            print(config.query('validation', check))
            print(config.query('validation', check, 'pass'))
            assert config.query('validation', check, 'pass'), f'{check} is not present or valid in the configuration file'
