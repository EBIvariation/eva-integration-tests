import os
import shutil

import yaml
from ebi_eva_common_pyutils.config import Configuration
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query

from utils.docker_utils import copy_files_to_container, copy_files_from_container, read_file_from_container, \
    run_command_in_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose


class TestEvaSubmissionIngestion(TestWithDockerCompose):
    vcf_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(TestWithDockerCompose.resources_directory, 'assembly_reports')

    vcf_file = os.path.join(vcf_files_dir, 'vcf_file_ASM294v2.vcf')
    vcf_file_name = os.path.basename(vcf_file)

    eload_config_file = os.path.join(TestWithDockerCompose.resources_directory, 'ELOAD_config.yml')

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_submission_test_run')
    metadata_xlsx = os.path.join(test_run_dir, 'metadata_xlsx.xlsx')
    metadata_json = os.path.join(test_run_dir, 'eva_sub_cli_metadata.json')

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-submission.yml')
    container_name = 'eva_submission_test'
    container_reference_genome_dir = '/opt/reference_sequences/nitrospira/GCA_000002945.2'
    container_eload_dir = '/opt/submissions'

    def setUp(self):
        super().setUp()
        self.container_log_files = []
        # create metadata xlsx file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'EVA_Submission_v2.0_cpombe.xlsx'),
            self.metadata_xlsx
        )

        # create metadata json file
        shutil.copyfile(
            os.path.join(self.resources_directory, 'metadata_files', 'eva_sub_cli_metadata.json'),
            self.metadata_json
        )

        self.eload_number = '1513'

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    def test_ingestion_archive_only(self):
        log_file = f'{self.container_eload_dir}/ELOAD_{self.eload_number}/ingestion.out'
        self.container_log_files.append(self.container_name, log_file)
        ingestion_cmd = (
            f"docker exec {self.container_name} sh -c 'ingest_submission.py --eload {self.eload_number} --tasks archive_only > {log_file} 2>&1'"
        )
        # Run ingestion from command line
        run_quiet_command("run eva_submission ingest_submission script", ingestion_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name, os.path.join(self.container_eload_dir), self.test_run_dir)

        # assert results
        self.assert_ingestion_archive_only_passed(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', f'.ELOAD_{self.eload_number}_config.yml'))

    def create_submission_dir_and_copy_files_to_container(self):
        # Prepare reference genome
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.assembly_reports_dir, 'GCA_000002945.2_assembly_report.txt'))
        copy_files_to_container(self.container_name, self.container_reference_genome_dir,
                                os.path.join(self.fasta_files_dir, 'GCA_000002945.2.fa'))

        # prepare eload folder with eload config file
        eload_config_template = os.path.join(self.resources_directory, 'ELOAD_configs',
                                             '.ELOAD_number_post_brokering.yml')
        with open(eload_config_template, 'r') as open_file:
            open_file_content = open_file.read().format(ELOAD_number=str(self.eload_number))
        eload_config_file = os.path.join(self.test_run_dir, f'.ELOAD_{self.eload_number}_config.yml')
        with open(eload_config_file, 'w') as open_file:
            open_file.write(open_file_content)
        eload_dir = os.path.join(self.container_eload_dir, f'ELOAD_{self.eload_number}')
        copy_files_to_container(self.container_name, eload_dir, eload_config_file)

        # compress and index the vcf file and put in 18_brokering
        copy_files_to_container(self.container_name, os.path.join(eload_dir, '18_brokering', 'ena'), self.vcf_file)
        vcf_file_in_container = os.path.join(eload_dir, '18_brokering', 'ena', self.vcf_file_name)
        run_command_in_container(self.container_name, f"bgzip -f {vcf_file_in_container}")
        run_command_in_container(self.container_name, f"bcftools index -c {vcf_file_in_container}.gz")

        # make public ftp directory
        yaml_content = read_file_from_container(self.container_name, os.path.join('/root', '.submission_config.yml'))
        submission_config = yaml.safe_load(yaml_content)
        run_command_in_container(self.container_name, f"mkdir -p {submission_config['public_ftp_dir']}")

    def assert_ingestion_archive_only_passed(self, eload_config_yml):
        # Check that the config file exists
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)

        # assert ingestion section in config
        assert config.query('ingestion', 'ena_load') == 'success'
        assert config.query('ingestion', 'ingestion_date') is not None
        assert config.query('ingestion', 'simple_archive', 'nextflow_dir', 'archive_only') == '<complete>'

        # assert files copied to 30_eva_valid and 60_eva_public and public ftp
        compress_vcf_file = f'{self.vcf_file_name}.gz'
        index_vcf_file = f'{compress_vcf_file}.csi'
        assert os.path.isfile(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '30_eva_valid', compress_vcf_file))
        assert os.path.isfile(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '30_eva_valid', index_vcf_file))
        assert os.path.isfile(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '60_eva_public', compress_vcf_file))
        assert os.path.isfile(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '60_eva_public', index_vcf_file))
        # assert files copied to public ftp
        yaml_content_submission_config = read_file_from_container(self.container_name,
                                                                  os.path.join('/root', '.submission_config.yml'))
        submission_config = yaml.safe_load(yaml_content_submission_config)
        eload_config = Configuration(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', f'.ELOAD_{self.eload_number}_config.yml'))
        public_compress_file_path = os.path.join(submission_config['public_ftp_dir'],
                                                 eload_config.query('brokering', 'ena', 'PROJECT'), compress_vcf_file)
        run_quiet_command("run copy command to copy from public ftp",
                          f"docker cp {self.container_name}:{public_compress_file_path} {self.test_run_dir}")
        assert os.path.isfile(os.path.join(self.test_run_dir, compress_vcf_file))
        public_index_file_path = os.path.join(submission_config['public_ftp_dir'],
                                              eload_config.query('brokering', 'ena', 'PROJECT'), index_vcf_file)
        run_quiet_command("run copy command to copy from public ftp",
                          f"docker cp {self.container_name}:{public_index_file_path} {self.test_run_dir}")
        assert os.path.isfile(os.path.join(self.test_run_dir, index_vcf_file))

        # assert data from ena loaded to evapro
        settings_file = os.path.join(self.resources_directory, 'maven-settings.xml')
        with get_metadata_connection_handle('docker', settings_file) as metadata_connection_handle:
            query = "select project_accession, taxonomy_id from evapro.project_taxonomy"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 4530)]
            assert set(results) == set(expected)

            query = "select eva_submission_id, eva_submission_status_id from evapro.eva_submission"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1513, 6)]
            assert set(results) == set(expected)

            query = "select project_accession, old_ticket_id, eload_id from evapro.project_eva_submission"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 1513, 1513)]
            assert set(results) == set(expected)

            query = "select project_accession, alias from evapro.project"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 'ELOAD_1513')]
            assert set(results) == set(expected)

            query = "select project_accession, submission_id from evapro.project_ena_submission"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 1)]
            assert set(results) == set(expected)

            query = "select taxonomy_id, common_name, scientific_name, taxonomy_code, eva_name from evapro.taxonomy"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(4530, 'Asian cultivated rice', 'Oryza sativa', 'osativa', 'Asian cultivated rice')]
            assert set(results) == set(expected)

            query = "select submission_id, submission_accession, type from evapro.submission"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'ERA35393650', 'PROJECT')]
            assert set(results) == set(expected)

            query = "select assembly_set_id, taxonomy_id, assembly_name, assembly_code from evapro.assembly_set"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 4530, 'IRGSP-1.0', 'irgsp10')]
            assert set(results) == set(expected)

            query = "select assembly_set_id, assembly_accession, assembly_chain, assembly_version from evapro.accessioned_assembly"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'GCA_001433935.1', 'GCA_001433935', 1)]
            assert set(results) == set(expected)

            query = "select analysis_accession, vcf_reference_accession, assembly_set_id from evapro.analysis"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 'GCA_001433935.1', 1)]
            assert set(results) == set(expected)

            query = "select project_accession, analysis_accession from evapro.project_analysis"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 'ERZ28769990')]
            assert set(results) == set(expected)

            query = "select experiment_type_id, experiment_type from evapro.experiment_type"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'Whole genome sequencing')]
            assert set(results) == set(expected)

            query = "select analysis_accession, submission_id from evapro.analysis_submission"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 1)]
            assert set(results) == set(expected)

            query = "select analysis_accession, experiment_type_id from evapro.analysis_experiment_type"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 1)]
            assert set(results) == set(expected)

            query = "select analysis_accession, file_id from evapro.analysis_file"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 1), ('ERZ28769990', 2)]
            assert set(results) == set(expected)

            query = "select project_accession, sample_count, pro_samp1_id from evapro.project_samples_temp1"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 0, 43)]
            assert set(results) == set(expected)

            query = "select project_accession, taxonomy_ids from evapro.project_children_taxonomy"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', '4530')]
            assert set(results) == set(expected)

            query = "select project_accession, reference_accession from evapro.project_reference"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 'GCA_001433935.1')]
            assert set(results) == set(expected)

            query = "select sample_id, biosample_accession, ena_accession from evapro.sample"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'SAMD00045866', 'DRS029882'), (2, 'SAMD00045867', 'DRS029883'),
                        (3, 'SAMD00045868', 'DRS029884'), (4, 'SAMD00045869', 'DRS029885'),
                        (5, 'SAMD00045870', 'DRS029886')]
            assert set(results) == set(expected)

            query = "select file_id, ena_submission_file_id, file_md5, file_type, file_size  from evapro.file"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'ERF219841043', '77b3f2576319887b36479474c39bf5e6', 'VCF', 50824503470),
                        (2, 'ERF219841044', 'bbca217c4ca11a8068b11fb9fb051a5e', 'CSI', 335146)]
            assert set(results) == set(expected)
