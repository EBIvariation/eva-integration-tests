import json
import os
import shutil

import yaml

from tests.components.eva_sub_cli.test_eva_sub_cli import TestEvaSubCli
from utils.docker_utils import copy_files_to_container, copy_files_from_container, read_file_from_container
from utils.test_utils import run_quiet_command


class TestEvaSubCliValidation(TestEvaSubCli):

    def test_native_validator_with_json(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_validation_json_metadata()
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)

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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_json)

    def test_native_validator_with_xlsx(self):
        # create metadata xlsx file and copy to container
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'EVA_Submission_Docker_Test.xlsx'),
            self.metadata_xlsx
        )
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_xlsx)

    def test_native_validator_with_files_on_command_line(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_validation_json_metadata_without_files()
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)

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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_json)

    def test_native_validator_with_multiple_analysis_files_on_command_line(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_validation_json_metadata_multiple_analysis_without_files()
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)

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
        # assert results - validation should fail
        # TODO update this to assert the expected failure
        self.assert_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json(),
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_json)

    def test_native_validator_with_tasks(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_validation_json_metadata()
        with open(self.metadata_json, 'w') as open_metadata:
            json.dump(sub_metadata, open_metadata)
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_json)

        validation_cmd = (
            f"docker exec {self.container_name} eva-sub-cli.py --executor=NATIVE --tasks=VALIDATE "
            f"--validation_tasks metadata_check sample_check "
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
        self.assert_partial_validation_results(self.get_expected_sample(), self.get_expected_metadata_files_json(),
                                               'Validation passed successfully.', self.get_expected_semantic_val())

    def test_docker_validator_with_json(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_validation_json_metadata()
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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_json)

    def test_docker_validator_with_json_existing_project(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_validation_json_metadata_existing_project()
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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_json)

    def test_docker_validator_with_json_containing_non_vcf_files(self):
        # create metadata json file and copy to container
        sub_metadata = self.get_validation_json_metadata_with_non_vcf_file()
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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_json)

    def test_docker_validator_with_xlsx(self):
        # create metadata xlsx file and copy to container
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'EVA_Submission_Docker_Test.xlsx'),
            self.metadata_xlsx
        )
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_xlsx)

    def test_docker_validator_with_xlsx_existing_project(self):
        # create metadata xlsx file and copy to container
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files',
                         'EVA_Submission_test_with_project_accession.xlsx'),
            self.metadata_xlsx
        )
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_xlsx)

    def test_docker_validator_with_xlsx_non_vcf_files(self):
        # create metadata xlsx file and copy to container
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files',
                         'EVA_Submission_Docker_Test_with_extra_files.xlsx'),
            self.metadata_xlsx
        )
        copy_files_to_container(self.container_name, self.container_submission_dir, self.metadata_xlsx)

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
                                       'Validation passed successfully.', self.get_expected_semantic_val(),
                                       self.metadata_xlsx)

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
                                  expected_metadata_val, expected_semantic_val, metadata_type):
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

        # assert metadata json post validation does not contain any non-vcf files
        if metadata_type.endswith('json'):
            generated_metadata_file_path = os.path.join(self.container_submission_dir, os.path.basename(metadata_type))
        elif metadata_type.endswith('xlsx'):
            generated_metadata_file_path = os.path.join(self.container_submission_dir, "validation_output",
                                                        "metadata.json")

        generated_metadata_json = json.loads(
            read_file_from_container(self.container_name, generated_metadata_file_path))
        for file in generated_metadata_json.get('files'):
            assert self.is_vcf_file(file['fileName'])
            assert 'md5' in file and file['md5'] != ''
            assert 'fileSize' in file and file['fileSize'] != ''

    def assert_partial_validation_results(self, expected_sample_checker, expected_metadata_files_json,
                                          expected_metadata_val, expected_semantic_val):
        validation_output_dir = self.eva_sub_cli_test_run_dir

        # VCF check wasn't run
        vcf_format_dir = os.path.join(validation_output_dir, 'vcf_format')
        self.assertFalse(os.path.exists(vcf_format_dir))
        vcf_format_log_file = os.path.join(vcf_format_dir, 'input_passed.vcf.vcf_format.log')
        self.assertFalse(os.path.exists(vcf_format_log_file))

        # Assembly check wasn't run
        assembly_check_dir = os.path.join(validation_output_dir, 'assembly_check')
        self.assertFalse(os.path.exists(assembly_check_dir))
        assembly_check_log_file = os.path.join(assembly_check_dir, 'input_passed.vcf.assembly_check.log')
        self.assertFalse(os.path.exists(assembly_check_log_file))

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

    def is_vcf_file(self, file_path):
        if file_path:
            file_path = file_path.strip().lower()
            return file_path.endswith('.vcf') or file_path.endswith('.vcf.gz')
        return False
