import json
import os
import random
import shutil
import subprocess

import yaml
from ebi_eva_common_pyutils.config import Configuration
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query

from tests.components.eva_submission.test_eva_submission import TestEvaSubmission
from utils.docker_utils import copy_files_to_container, copy_files_from_container, read_file_from_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import log_on_failure


class TestEvaSubmissionBrokering(TestEvaSubmission):
    def setUp(self):
        self.webin_username = os.environ.get('EVA_SUBMISSION_WEBIN_USERNAME')
        self.webin_password = os.environ.get('EVA_SUBMISSION_WEBIN_PASSWORD')
        if not self.webin_username or not self.webin_password:
            self.fail('EVA_SUBMISSION_WEBIN_USERNAME or EVA_SUBMISSION_WEBIN_PASSWORD not set')

        super().setUp()

        # create metadata xlsx file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'EVA_Submission_v3.1.0_cpombe.xlsx'),
            self.metadata_xlsx
        )
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'EVA_Submission_v1.1.4_cpombe.xlsx'),
            self.old_metadata_xlsx
        )
        # create metadata json file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'eva_sub_cli_metadata.json'),
            self.metadata_json
        )
        # The ELOAD number is used to generate the project alias which needs to be unique on ENA's side.
        # ENA's test server should delete the submissions every 24 hours
        # Probability that we use the same ELOAD number twice over 24 hours is low
        self.eload_number1 = random.randint(1, 1000000)
        self.eload_number2 = random.randint(1, 1000000)
        self.eload_number3 = random.randint(1, 1000000)
        self.eload_number4 = random.randint(1, 1000000)
        self.eload_number5 = random.randint(1, 1000000)
        self.eload_number6 = random.randint(1, 1000000)

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    @log_on_failure
    def test_submission_with_new_metadata_spreadsheet(self):
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 --eload {self.eload_number1}"
        )

        # Run preparation from command line
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        # get submission id from the table
        submission_id = self.get_submission_id_from_db(self.eload_number1)

        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --submission_id {submission_id} > {self.container_submission_dir}/{submission_id}/validation.out 2>&1'"
        )
        # Run validation from command line
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        log_file = f'{self.container_submission_dir}/{submission_id}/broker.out'
        self.container_log_files.append((self.container_name, log_file))
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --debug --submission_id {submission_id} > {log_file} 2>&1'"
        )
        # Run brokering from command line
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name, self.container_submission_dir, self.test_run_dir)

        # assert results
        submission_config_file = os.path.join(self.test_run_dir, f'{submission_id}',
                                         f'.{submission_id}_config.yml')
        self.assert_brokering_pass_in_config(submission_config_file)

        config = Configuration(submission_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None
        self.assert_submission_processing_status_updated(submission_id, 'BROKERING', 'SUCCESS')
        self.assert_submission_details_updated(submission_id)

    @log_on_failure
    def test_submission_with_old_metadata_spreadsheet(self):
        submission_id = f'ELOAD_{self.eload_number2}'
        self.put_submission_in_db(submission_id, self.eload_number2)

        log_file = f'{self.container_submission_dir}/{submission_id}/broker.out'
        self.container_log_files.append((self.container_name, log_file))
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --debug --submission_id {submission_id} > {log_file} 2>&1'"
        )
        # Run brokering from command line
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name, self.container_submission_dir, self.test_run_dir)

        # assert results
        self.assert_brokering_pass_in_config(
            os.path.join(self.test_run_dir, f'{submission_id}', f'.{submission_id}_config.yml'))

    @log_on_failure
    def test_submission_with_existing_project(self):
        submission_id = f'ELOAD_{self.eload_number3}'
        self.put_submission_in_db(submission_id, self.eload_number3)

        log_file = f'{self.container_submission_dir}/{submission_id}/broker.out'
        self.container_log_files.append((self.container_name, log_file))
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --debug --submission_id {submission_id} --project_accession PRJEB12770 > {log_file} 2>&1'"
        )
        # Run brokering from command line
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name, self.container_submission_dir, self.test_run_dir)

        # assert results
        submission_config_file = os.path.join(self.test_run_dir, f'{submission_id}', f'.{submission_id}_config.yml')
        self.assert_brokering_pass_in_config(submission_config_file)
        # The sample was created in BioSamples from the bioSampleObject
        sample_record = self.get_sample_records(submission_config_file)[0]
        assert sample_record['analysisAlias'] == ['AA']
        assert sample_record['name'] == 'S1'
        assert sample_record['action'] == 'create'
        self.assert_metadata_json_updated_with_sample_records(submission_id, submission_config_file)

    @log_on_failure
    def test_submission_with_pre_registered_samples(self):
        # Broker a first submission to get a sample registered in BioSamples
        submission_id1 = f'ELOAD_{self.eload_number3}'
        self.put_submission_in_db(submission_id1, self.eload_number3)
        log_file = f'{self.container_submission_dir}/{submission_id1}/broker.out'
        self.container_log_files.append((self.container_name, log_file))
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --debug --submission_id {submission_id1} --project_accession PRJEB12770 > {log_file} 2>&1'"
        )
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)
        copy_files_from_container(self.container_name, self.container_submission_dir, self.test_run_dir)
        submission_config_file1 = os.path.join(self.test_run_dir, submission_id1, f'.{submission_id1}_config.yml')
        sample_accession = self.get_sample_records(submission_config_file1)[0]['accession']

        # Second submission referencing the sample by its accession only
        submission_id2 = f'ELOAD_{self.eload_number6}'
        self.put_submission_in_db(submission_id2, self.eload_number6, create_account=False)
        self.copy_submission_with_metadata_json_to_container(
            self.eload_number6,
            {'analysisAlias': ['AA'], 'sampleInVCF': 'S1', 'bioSampleAccession': sample_accession}
        )
        log_file = f'{self.container_submission_dir}/{submission_id2}/broker.out'
        self.container_log_files.append((self.container_name, log_file))
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --debug --submission_id {submission_id2} --project_accession PRJEB12770 > {log_file} 2>&1'"
        )
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)
        copy_files_from_container(self.container_name, self.container_submission_dir, self.test_run_dir)

        # assert results
        submission_config_file2 = os.path.join(self.test_run_dir, submission_id2, f'.{submission_id2}_config.yml')
        self.assert_brokering_pass_in_config(submission_config_file2)
        # The sample was not modified and its name was retrieved from BioSamples
        assert self.get_sample_records(submission_config_file2) == [{
            'accession': sample_accession, 'analysisAlias': ['AA'], 'sampleInVCF': 'S1', 'name': 'S1', 'action': 'None'
        }]
        self.assert_metadata_json_updated_with_sample_records(submission_id2, submission_config_file2)

    @log_on_failure
    def test_submission_with_ena_xml(self):
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 --eload {self.eload_number4}"
        )

        # Run preparation from command line
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        # get submission id from the table
        submission_id = self.get_submission_id_from_db(self.eload_number4)

        log_file = f'{self.container_submission_dir}/{submission_id}/validation.out'
        self.container_log_files.append((self.container_name, log_file))
        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --submission_id {submission_id} > {log_file} 2>&1'"
        )
        # Run validation from command line
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        log_file = f'{self.container_submission_dir}/{submission_id}/broker.out'
        self.container_log_files.append((self.container_name, log_file))
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --debug --submission_id {submission_id} --output_format xml > {log_file} 2>&1'"
        )
        # Run brokering from command line
        run_quiet_command("run eva_submission broker_submission script", brokering_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name,
                                  self.container_submission_dir,
                                  self.test_run_dir)

        # assert results
        submission_config_file = os.path.join(self.test_run_dir, f'{submission_id}',
                                         f'.{submission_id}_config.yml')
        self.assert_brokering_pass_in_config(submission_config_file)

        config = Configuration(submission_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None
        self.assert_submission_processing_status_updated(submission_id, 'BROKERING', 'SUCCESS')
        self.assert_submission_details_updated(submission_id)

    @log_on_failure
    def test_brokering_crash_records_status(self):
        # Run prepare and validate
        prepare_cmd = (
            f"docker exec {self.container_name} prepare_submission.py --submitter username --ftp_box 1 --eload {self.eload_number5}"
        )
        run_quiet_command("run eva_submission prepare_submission script", prepare_cmd)

        # get submission id from the table
        submission_id = self.get_submission_id_from_db(self.eload_number5)

        validation_cmd = (
            f"docker exec {self.container_name} sh -c 'validate_submission.py --submission_id {submission_id} > {self.container_submission_dir}/{submission_id}/validation.out 2>&1'"
        )
        run_quiet_command("run eva_submission validate_submission script", validation_cmd)

        # Overwrite Webin credentials with incorrect ones
        yaml_content = read_file_from_container(self.container_name,
                                                os.path.join('/root', '.submission_config.yml'))
        submission_config = yaml.safe_load(yaml_content)
        submission_config['ena'].update({'username': 'wrong_user', 'password': 'wrong_password'})

        tmp_yml = os.path.join(self.test_run_dir, '.submission_config.yml')
        with open(tmp_yml, 'w') as open_file:
            yaml.safe_dump(submission_config, open_file)
        copy_files_to_container(self.container_name, '/root', tmp_yml)
        os.remove(tmp_yml)

        # Run brokering, should fail but still update the status
        log_file = f'{self.container_submission_dir}/{submission_id}/broker.out'
        self.container_log_files.append((self.container_name, log_file))
        brokering_cmd = (
            f"docker exec {self.container_name} sh -c 'broker_submission.py --use_legacy_upload --debug --submission_id {submission_id} --output_format xml > {log_file} 2>&1'"
        )
        try:
            run_quiet_command("run eva_submission broker_submission script", brokering_cmd)
            # command should crash so we don't get here
            assert False
        except subprocess.CalledProcessError:
            copy_files_from_container(self.container_name, self.container_submission_dir,
                                      self.test_run_dir)
            submission_config_file = os.path.join(self.test_run_dir, f'{submission_id}',
                                             f'.{submission_id}_config.yml')
            config = Configuration(submission_config_file)
            submission_id = config.query('submission', 'submission_id')
            assert submission_id is not None
            self.assert_submission_processing_status_updated(submission_id, 'BROKERING', 'FAILURE')

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

        # Prepare reference genome
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.assembly_reports_dir, 'GCA_000002945.2_assembly_report.txt'))
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.fasta_files_dir, 'GCA_000002945.2.fa'))

        vcf_file = os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
        copy_files_to_container(self.container_name, self.container_ftp_submission_dir, vcf_file)
        if self.metadata_xlsx:
            copy_files_to_container(self.container_name, self.container_ftp_submission_dir, self.metadata_xlsx)

        # Prepared Submission with old spreadsheet
        submission_config_template = os.path.join(self.resources_directory, 'ELOAD_configs',
                                             '.ELOAD_number_post_validation_spreadsheet.yml')
        with open(submission_config_template, 'r') as open_file:
            open_file_content = open_file.read().format(ELOAD_number=str(self.eload_number2))
        submission_config_file = os.path.join(self.test_run_dir, f'.ELOAD_{self.eload_number2}_config.yml')
        with open(submission_config_file, 'w') as open_file:
            open_file.write(open_file_content)
        eload2_dir = os.path.join(self.container_submission_dir, f'ELOAD_{self.eload_number2}')
        copy_files_to_container(self.container_name, eload2_dir, submission_config_file)
        copy_files_to_container(self.container_name, os.path.join(eload2_dir, '10_submitted', 'vcf_files'), vcf_file)
        copy_files_to_container(self.container_name, os.path.join(eload2_dir, '10_submitted', 'metadata_file'),
                                self.old_metadata_xlsx)

        # Prepared Submission for existing project
        submission_config_template = os.path.join(self.resources_directory, 'ELOAD_configs',
                                             '.ELOAD_number_post_validation_json.yml')
        with open(submission_config_template, 'r') as open_file:
            open_file_content = open_file.read().format(ELOAD_number=str(self.eload_number3))
        submission_config_file = os.path.join(self.test_run_dir, f'.ELOAD_{self.eload_number3}_config.yml')
        with open(submission_config_file, 'w') as open_file:
            open_file.write(open_file_content)
        eload3_dir = os.path.join(self.container_submission_dir, f'ELOAD_{self.eload_number3}')
        copy_files_to_container(self.container_name, eload3_dir, submission_config_file)
        copy_files_to_container(self.container_name, os.path.join(eload3_dir, '10_submitted', 'vcf_files'), vcf_file)
        copy_files_to_container(self.container_name, os.path.join(eload3_dir, '10_submitted', 'metadata_file'),
                                self.metadata_json)

    def assert_brokering_pass_in_config(self, eload_config_yml):
        # Check that the config file exists
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)

        # BioSample brokering passes and records the sample present in the VCF
        assert config.query('brokering', 'Biosamples', 'pass') is True
        assert config.query('brokering', 'Biosamples', 'Samples') is None
        sample_records = config.query('brokering', 'Biosamples', 'sample_records', ret_default=[])
        assert len(sample_records) == 1
        assert sample_records[0]['accession'].startswith('SAMEA')
        assert sample_records[0]['sampleInVCF'] == 'S1'
        assert sample_records[0]['analysisAlias']

        # ENA brokering passes
        assert config.query('brokering', 'ena', 'pass') is True
        assert config.query('brokering', 'ena', 'PROJECT', ret_default='').startswith('PRJE')

    def assert_submission_details_updated(self, submission_id):
        metadata_connection_handle = get_metadata_connection_handle(self.maven_profile, self.maven_settings_file)
        with metadata_connection_handle:
            submission_details_query = (f"SELECT release_date, project_accession "
                                        f"FROM eva_submissions.submission_tracking_details "
                                        f"where submission_id = '{submission_id}'")
            results = get_all_results_for_query(metadata_connection_handle, submission_details_query)
            assert len(results) == 1
            release_date, project_accession = results[0]
            assert release_date is not None
            assert project_accession is not None and project_accession.startswith('PRJE')

            analysis_accessions_query = (f"SELECT analysis_accessions "
                                        f"FROM eva_submissions.submission_tracking_details_analysis_accessions "
                                        f"where submission_id = '{submission_id}'")
            results = get_all_results_for_query(metadata_connection_handle, analysis_accessions_query)
            assert len(results) > 0
            analysis_accessions = [r[0] for r in results]
            assert analysis_accessions[0].startswith('ERZ')

    @staticmethod
    def get_sample_records(eload_config_yml):
        return Configuration(eload_config_yml).query('brokering', 'Biosamples', 'sample_records')

    def assert_metadata_json_updated_with_sample_records(self, submission_id, eload_config_yml):
        # The metadata sent to ENA contains the accessions from the sample records, in the same order
        brokering_json = os.path.join(self.test_run_dir, submission_id, '18_brokering', 'ena', 'metadata_json.json')
        with open(brokering_json) as open_file:
            samples = json.load(open_file)['sample']
        sample_records = self.get_sample_records(eload_config_yml)
        assert [sample['bioSampleAccession'] for sample in samples] == [r['accession'] for r in sample_records]
        assert [sample['sampleInVCF'] for sample in samples] == [r['sampleInVCF'] for r in sample_records]
        assert [sample['analysisAlias'] for sample in samples] == [[f'{submission_id}_AA']]

    def copy_submission_with_metadata_json_to_container(self, eload_number, sample):
        """Create a validated submission whose metadata JSON contains a single sample."""
        with open(self.metadata_json) as open_file:
            metadata_json = json.load(open_file)
        metadata_json['sample'] = [sample]
        eload_metadata_json = os.path.join(self.test_run_dir, f'ELOAD_{eload_number}', 'eva_sub_cli_metadata.json')
        os.makedirs(os.path.dirname(eload_metadata_json), exist_ok=True)
        with open(eload_metadata_json, 'w') as open_file:
            json.dump(metadata_json, open_file)

        submission_config_template = os.path.join(self.resources_directory, 'ELOAD_configs',
                                                  '.ELOAD_number_post_validation_json.yml')
        with open(submission_config_template, 'r') as open_file:
            open_file_content = open_file.read().format(ELOAD_number=str(eload_number))
        submission_config_file = os.path.join(self.test_run_dir, f'.ELOAD_{eload_number}_config.yml')
        with open(submission_config_file, 'w') as open_file:
            open_file.write(open_file_content)
        eload_dir = os.path.join(self.container_submission_dir, f'ELOAD_{eload_number}')
        copy_files_to_container(self.container_name, eload_dir, submission_config_file)
        copy_files_to_container(self.container_name, os.path.join(eload_dir, '10_submitted', 'vcf_files'),
                                os.path.join(self.vcf_files_dir, 'vcf_file_ASM294v2.vcf'))
        copy_files_to_container(self.container_name, os.path.join(eload_dir, '10_submitted', 'metadata_file'),
                                eload_metadata_json)
