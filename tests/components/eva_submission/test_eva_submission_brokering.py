import os
import random
import shutil

import yaml
from ebi_eva_common_pyutils.config import Configuration

from utils.docker_utils import copy_files_to_container, copy_files_from_container, read_file_from_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose


class TestEvaSubmissionBrokering(TestWithDockerCompose):

    vcf_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(TestWithDockerCompose.resources_directory, 'assembly_reports')

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_submission_test_run')
    metadata_xlsx = os.path.join(test_run_dir, 'metadata_xlsx.xlsx')
    old_metadata_xlsx = os.path.join(test_run_dir, 'old_metadata_xlsx.xlsx')

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components', 'docker-compose-eva-submission.yml')
    container_name = 'eva_submission_test'
    container_reference_genome_dir = '/opt/reference_sequences/nitrospira/GCA_000002945.2'
    container_submission_dir = '/opt/ftp/private/eva-box-01/upload/username'
    container_eload_dir = '/opt/submissions'

    def setUp(self):
        self.webin_username = os.environ.get('EVA_SUBMISSION_WEBIN_USERNAME')
        self.webin_password = os.environ.get('EVA_SUBMISSION_WEBIN_PASSWORD')
        if not self.webin_username or not self.webin_password:
            self.fail('EVA_SUBMISSION_WEBIN_USERNAME or EVA_SUBMISSION_WEBIN_PASSWORD not set')
        super().setUp()
        # create metadata xlsx file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_spreadsheets', 'EVA_Submission_v2.0_cpombe.xlsx'),
            self.metadata_xlsx
        )
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_spreadsheets', 'EVA_Submission_v1.1.4_cpombe.xlsx'),
            self.old_metadata_xlsx
        )
        # The ELOAD number is used to generate the project alias which needs to be unique on ENA's side.
        # ENA's test server should delete the submissions every 24 hours
        # Probability that we use the same ELOAD number twice over 24 hours is low
        self.eload_number1 = random.randint(1, 10000)
        self.eload_number2 = random.randint(1, 10000)
        self.eload_number3 = random.randint(1, 10000)

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    def test_submission_with_new_metadata_spreadsheet(self):
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 --eload {self.eload_number1}"
        )

        # Run preparation from command line
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --eload {self.eload_number1} > {self.container_eload_dir}/ELOAD_{self.eload_number1}/validation.out 2>&1'"
        )
        # Run validation from command line
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --eload {self.eload_number1} > {self.container_eload_dir}/ELOAD_{self.eload_number1}/broker.out 2>&1'"
        )
        # Run brokering from command line
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_eload_dir),
                                  self.test_run_dir)

        # assert results
        self.assert_brokering_pass_in_config(os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number1}', f'.ELOAD_{self.eload_number1}_config.yml'))


    def test_submission_with_old_metadata_spreadsheet(self):
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --eload {self.eload_number2} > {self.container_eload_dir}/ELOAD_{self.eload_number2}/broker.out 2>&1'"
        )
        # Run brokering from command line
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_eload_dir),
                                  self.test_run_dir)

        # assert results
        self.assert_brokering_pass_in_config(os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number2}', f'.ELOAD_{self.eload_number2}_config.yml'))

    def test_submission_with_existing_project(self):
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --eload {self.eload_number3} > {self.container_eload_dir}/ELOAD_{self.eload_number3}/broker.out 2>&1'"
        )
        # Run brokering from command line
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_eload_dir),
                                  self.test_run_dir)

        # assert results
        self.assert_brokering_pass_in_config(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number2}', f'.ELOAD_{self.eload_number2}_config.yml'))


    def create_submission_dir_and_copy_files_to_container(self):
        # Get the config file from the container and update the username and password for Webin
        yaml_content = read_file_from_container(self.container_name,
                                                os.path.join('/root', '.submission_config.yml'))
        submission_config = yaml.safe_load(yaml_content)
        submission_config['biosamples'].update({'webin_username': self.webin_username, 'webin_password': self.webin_password})
        submission_config['ena'].update({'username': self.webin_username, 'password': self.webin_password})

        tmp_yml =  os.path.join(self.test_run_dir, '.submission_config.yml')
        with open(tmp_yml, 'w') as open_file:
            yaml.safe_dump(submission_config, open_file)
        copy_files_to_container(self.container_name, '/root', tmp_yml)
        os.remove(tmp_yml)

        # Prepare reference genome
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.assembly_reports_dir, 'GCA_000002945.2_assembly_report.txt'))
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.fasta_files_dir, 'GCA_000002945.2.fa'))

        vcf_file = os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
        copy_files_to_container(self.container_name, self.container_submission_dir, vcf_file)
        if self.metadata_xlsx:
            copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

        # Prepared ELOAD with old spreadsheet
        eload_config_template = os.path.join(self.resources_directory, 'ELOAD_configs', '.ELOAD_number_post_validation.yml')
        with open(eload_config_template, 'r') as open_file:
            open_file_content = open_file.read().format(ELOAD_number=str(self.eload_number2))
        eload_config_file = os.path.join(self.test_run_dir, f'.ELOAD_{self.eload_number2}_config.yml')
        with open(eload_config_file, 'w') as open_file:
            open_file.write(open_file_content)
        eload2_dir = os.path.join(self.container_eload_dir, f'ELOAD_{self.eload_number2}')
        copy_files_to_container(self.container_name, eload2_dir, eload_config_file)
        copy_files_to_container(self.container_name, os.path.join(eload2_dir, '10_submitted', 'vcf_files'), vcf_file)
        copy_files_to_container(self.container_name, os.path.join(eload2_dir, '10_submitted', 'metadata_file'), self.old_metadata_xlsx)

        # Prepared ELOAD for existing project
        eload_config_template = os.path.join(self.resources_directory, 'ELOAD_configs',
                                             '.ELOAD_number_post_validation.yml')
        with open(eload_config_template, 'r') as open_file:
            open_file_content = open_file.read().format(ELOAD_number=str(self.eload_number3))
        eload_config_file = os.path.join(self.test_run_dir, f'.ELOAD_{self.eload_number3}_config.yml')
        with open(eload_config_file, 'w') as open_file:
            open_file.write(open_file_content)
        eload3_dir = os.path.join(self.container_eload_dir, f'ELOAD_{self.eload_number3}')
        copy_files_to_container(self.container_name, eload3_dir, eload_config_file)
        copy_files_to_container(self.container_name, os.path.join(eload3_dir, '10_submitted', 'vcf_files'), vcf_file)
        copy_files_to_container(self.container_name, os.path.join(eload3_dir, '10_submitted', 'metadata_file'), self.metadata_xlsx)

    def assert_brokering_pass_in_config(self, eload_config_yml):
        # Check that the config file exists
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)

        # BioSample brokering passes
        assert config.query('brokering', 'Biosamples', 'pass') is True
        assert config.query('brokering', 'Biosamples', 'Samples', 'S1', ret_default='').startswith('SAMEA')

        # ENA brokering passes
        assert config.query('brokering', 'ena', 'pass') is True
        assert config.query('brokering', 'ena', 'PROJECT', ret_default='').startswith('PRJE')
