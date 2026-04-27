import os
import shutil

import yaml
from ebi_eva_common_pyutils.config import Configuration

from tests.components.eva_submission.test_eva_submission import TestEvaSubmission
from utils.docker_utils import copy_files_to_container, copy_files_from_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import log_on_failure


class TestEvaSubmissionValidation(TestEvaSubmission):
    def setUp(self):
        super().setUp()
        
        # create metadata xlsx file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'EVA_Submission_v2.0_cpombe.xlsx'),
            self.metadata_xlsx
        )

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

        self.eload_number = 1

    @log_on_failure
    def test_submission_with_new_metadata_spreadsheet(self):
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 --eload {self.eload_number}"
        )

        # Run preparation from command line
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        log_file = f'{self.container_eload_dir}/ELOAD_{self.eload_number}/validation.out'
        self.container_log_files.append((self.container_name, log_file))
        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --eload {self.eload_number} > {log_file} 2>&1'"
        )
        # Run validation from command line
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_eload_dir),
                                  self.test_run_dir)
        # assert results
        eload_config_file = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}',
                                         f'.ELOAD_{self.eload_number}_config.yml')
        self.assert_validation_pass_in_config(eload_config_file)

        self.assert_directory_structure(os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}'))

        config = Configuration(eload_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None
        self.assert_submission_processing_status_updated(submission_id, 'VALIDATION', 'SUCCESS')

    @log_on_failure
    def test_validation_with_tasks(self):
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 "
            f"--eload {self.eload_number}"
        )

        # Run preparation from command line
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --eload {self.eload_number} "
            f"--validation_tasks metadata_check structural_variant_check "
            f"> {self.container_eload_dir}/ELOAD_{self.eload_number}/validation.out'"
        )
        # Run validation from command line
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_eload_dir),
                                  self.test_run_dir)
        # assert results
        eload_config_file = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}',
                                         f'.ELOAD_{self.eload_number}_config.yml')

        tasks = ['metadata_check', 'structural_variant_check']
        self.assert_validation_pass_in_config(eload_config_file, tasks=tasks)
        self.assert_directory_structure(os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}'), tasks=tasks)

        config = Configuration(eload_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None
        self.assert_submission_processing_status_updated(submission_id, 'VALIDATION', 'FAILURE')

    @log_on_failure
    def test_validation_tasks_results_are_not_overwritten(self):
        prepare_cmd = (f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 "
                       f"--eload {self.eload_number}")

        # Run preparation from command line
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        # Run first set of tasks
        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --eload {self.eload_number} "
            f"--validation_tasks metadata_check structural_variant_check "
            f"> {self.container_eload_dir}/ELOAD_{self.eload_number}/validation.out'"
        )
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        # Run the next set of tasks
        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --eload {self.eload_number} "
            f"--validation_tasks vcf_check naming_convention_check "
            f"> {self.container_eload_dir}/ELOAD_{self.eload_number}/validation.out'"
        )
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  os.path.join(self.container_eload_dir),
                                  self.test_run_dir)
        # assert results
        eload_config_file = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}',
                                         f'.ELOAD_{self.eload_number}_config.yml')
        tasks = ['vcf_check', 'metadata_check', 'structural_variant_check', 'naming_convention_check']
        self.assert_validation_pass_in_config(eload_config_file, tasks=tasks)
        self.assert_directory_structure(os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}'), tasks=tasks)

        config = Configuration(eload_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None
        self.assert_submission_processing_status_updated(submission_id, 'VALIDATION', 'FAILURE')

    def create_submission_dir_and_copy_files_to_container(self):
        vcf_file = os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
        copy_files_to_container(self.container_name, self.container_submission_dir, vcf_file)
        if self.metadata_xlsx:
            copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

        # Prepare reference genome
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.assembly_reports_dir, 'GCA_000002945.2_assembly_report.txt'))
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.fasta_files_dir, 'GCA_000002945.2.fa'))

    def assert_validation_pass_in_config(self, eload_config_yml, tasks=[
        'vcf_check', 'assembly_check', 'metadata_check', 'sample_check', 'structural_variant_check',
        'naming_convention_check'
    ]):
        # Check that the config file exists
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)
        # Check that each validation does pass
        for check in tasks:
            print(check)
            print(config.query('validation'))
            print(config.query('validation', check))
            print(config.query('validation', check, 'pass'))
            assert config.query('validation', check,
                                'pass'), f'{check} is not present or valid in the configuration file'

    def assert_directory_structure(self, eload_folder, tasks=[
        'vcf_check', 'assembly_check', 'metadata_check', 'sample_check', 'structural_variant_check',
        'naming_convention_check'
    ]):
        # Check that the eva-sub-cli output file have been copied to the 13_validation folder
        report_txt = os.path.join(eload_folder, '13_validation', 'eva_sub_cli', 'validation_submission_dir',
                                  'validation_output', 'report.txt')
        assert os.path.isfile(report_txt)
        result_yaml = os.path.join(eload_folder, '13_validation', 'eva_sub_cli', 'validation_submission_dir',
                                   'validation_results.yaml')
        assert os.path.isfile(result_yaml)
        with open(result_yaml) as open_file:
            cli_results = yaml.safe_load(open_file)
        if 'assembly_check' in tasks:
            assembly_report_path = cli_results['assembly_check']['vcf_file_ASM294v2.vcf']['report_path'].replace(
                self.container_eload_dir, self.test_run_dir)
            assert os.path.isfile(assembly_report_path)
        if 'metadata_check' in tasks:
            metadata_report_path = cli_results['metadata_check']['json_report_path'].replace(
                self.container_eload_dir, self.test_run_dir)
            assert os.path.isfile(metadata_report_path)
