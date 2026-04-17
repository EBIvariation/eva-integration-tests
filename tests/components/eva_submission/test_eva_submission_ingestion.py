import os
import shutil

import yaml
from ebi_eva_common_pyutils.config import Configuration
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.mongo_utils import get_mongo_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query, execute_query

from tests.components.eva_submission.test_eva_submission import TestEvaSubmission
from utils.docker_utils import copy_files_to_container, copy_files_from_container, read_file_from_container, \
    run_command_in_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import log_on_failure


class TestEvaSubmissionIngestion(TestEvaSubmission):
    vcf_file = os.path.join(TestEvaSubmission.vcf_files_dir, 'vcf_file_ASM294v2.vcf')
    vcf_file_name = os.path.basename(vcf_file)

    # same as in tests/resources/.ELOAD_number_post_brokering.yml
    submission_id = '43092992-2a33-4f98-a854-88322558f9c2'
    submission_account_id = "test_submission_account"

    def setUp(self):
        super().setUp()

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

    @log_on_failure
    def test_ingestion_archive_only(self):
        log_file = f'{self.container_eload_dir}/ELOAD_{self.eload_number}/ingestion.out'
        self.container_log_files.append((self.container_name, log_file))
        ingestion_cmd = (
            f"docker exec {self.container_name} sh -c 'ingest_submission.py --eload {self.eload_number} --tasks archive_only > {log_file} 2>&1'"
        )
        # Run ingestion from command line
        run_quiet_command("run eva_submission ingest_submission script for archive_only", ingestion_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name, os.path.join(self.container_eload_dir), self.test_run_dir)

        # assert results
        eload_config_file = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', f'.ELOAD_{self.eload_number}_config.yml')
        self.assert_ingestion_archive_only(eload_config_file)

        config = Configuration(eload_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None
        self.assert_submission_processing_status_updated(submission_id, 'INGESTION', 'FAILURE')

    @log_on_failure
    def test_ingestion_variant_load_and_accession(self):
        log_file = f'{self.container_eload_dir}/ELOAD_{self.eload_number}/ingestion.out'
        self.container_log_files.append((self.container_name, log_file))
        ingestion_cmd = (
            f"docker exec {self.container_name} sh -c 'ingest_submission.py --eload {self.eload_number} --tasks metadata_load variant_load accession > {log_file} 2>&1'"
        )
        # Run ingestion from command line
        run_quiet_command("run eva_submission ingest_submission script for variant_load and accession", ingestion_cmd)

        # copy validation output from docker
        copy_files_from_container(self.container_name, os.path.join(self.container_eload_dir), self.test_run_dir)

        # assert results
        eload_config_file = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', f'.ELOAD_{self.eload_number}_config.yml')
        self.assert_ingestion_variant_load_and_accession(eload_config_file)

        config = Configuration(eload_config_file)
        submission_id = config.query('submission', 'submission_id')
        assert submission_id is not None
        self.assert_submission_processing_status_updated(submission_id, 'INGESTION', 'FAILURE')

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

        # insert data in eva-submission-ws tables
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            # insert submission account
            submission_account_query = (
                f"INSERT INTO eva_submissions.submission_account (id, first_name, last_name, login_type, primary_email, user_id) "
                f"VALUES('{self.submission_account_id}', 'Test', 'User', 'webin', 'test-user@email.com', '{self.submission_account_id}')")
            execute_query(metadata_connection_handle, submission_account_query)

            # insert submission
            submission_query = (
                f"INSERT INTO eva_submissions.submission (submission_id, completion_time, initiation_time, status, upload_url, uploaded_time, submission_account_id) "
                f"VALUES('{self.submission_id}', NULL, '2025-05-21 18:43:25.384', 'UPLOADED', 'test-upload-url', '2025-05-21 19:10:30.232', '{self.submission_account_id}')")
            execute_query(metadata_connection_handle, submission_query)

    def assert_ingestion_archive_only(self, eload_config_yml):
        # Check that the config file exists
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)

        # assert ingestion section in config
        assert config.query('ingestion', 'ena_load') == 'success'
        assert config.query('ingestion', 'ingestion_date') is not None
        assert config.query('ingestion', 'simple_archive', 'nextflow_dir', 'archive_only') == '<complete>'

        compress_vcf_file = f'{self.vcf_file_name}.gz'
        index_vcf_file = f'{compress_vcf_file}.csi'

        # assert files copied to 30_eva_valid, 60_eva_public
        eva_30_valid_dir = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '30_eva_valid')
        assert os.path.isfile(os.path.join(eva_30_valid_dir, compress_vcf_file))
        assert os.path.isfile(os.path.join(eva_30_valid_dir, index_vcf_file))
        eva_60_public_dir = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '60_eva_public')
        assert os.path.isfile(os.path.join(eva_60_public_dir, compress_vcf_file))
        assert os.path.isfile(os.path.join(eva_60_public_dir, index_vcf_file))

        # assert files copied to public ftp
        public_ftp_dir = self.get_public_ftp_dir()
        self.assert_file_copied_to_public_ftp(public_ftp_dir, compress_vcf_file)
        self.assert_file_copied_to_public_ftp(public_ftp_dir, index_vcf_file)

        # assert data from ena loaded to evapro
        self.assert_data_from_ena_loaded_to_evapro()

    def assert_ingestion_variant_load_and_accession(self, eload_config_yml):
        # Check that the config file exists
        assert os.path.isfile(eload_config_yml)
        config = Configuration(eload_config_yml)

        # assert brokering section in config
        assert config.query('brokering', 'ena', 'hold_date') is not None
        # assert ingestion section in config
        assert config.query('ingestion', 'ena_load') == 'success'
        assert config.query('ingestion', 'ingestion_date') is not None
        assert config.query('ingestion', 'accession_and_load', 'nextflow_dir', 'accession') == '<complete>'
        assert config.query('ingestion', 'accession_and_load', 'nextflow_dir', 'variant_load') == '<complete>'
        assert config.query('ingestion', 'project_dir') == '/opt/submissions/ELOAD_1513'
        assert config.query('ingestion', 'database', 'GCA_000002945.2', 'db_name') == 'eva_spombe_asm294v2'
        assert config.query('ingestion', 'vep', 'GCA_000002945.2', 'cache_version') == 62
        assert config.query('ingestion', 'vep', 'GCA_000002945.2', 'species') == 'schizosaccharomyces_pombe'
        assert config.query('ingestion', 'vep', 'GCA_000002945.2', 'version') == 115

        compress_vcf_file = f'{self.vcf_file_name}.gz'
        index_vcf_file = f'{compress_vcf_file}.csi'
        accessioned_vcf_file = f'{os.path.splitext(self.vcf_file_name)[0]}.accessioned.vcf.gz'
        accessioned_index_file = f'{accessioned_vcf_file}.csi'

        # assert files copied to 30_eva_valid, 60_eva_public
        eva_30_valid_dir = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '30_eva_valid')
        assert os.path.isfile(os.path.join(eva_30_valid_dir, compress_vcf_file))
        assert os.path.isfile(os.path.join(eva_30_valid_dir, index_vcf_file))
        eva_60_public_dir = os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', '60_eva_public')
        assert os.path.isfile(os.path.join(eva_60_public_dir, compress_vcf_file))
        assert os.path.isfile(os.path.join(eva_60_public_dir, index_vcf_file))
        assert os.path.isfile(os.path.join(eva_60_public_dir, accessioned_vcf_file))
        assert os.path.isfile(os.path.join(eva_60_public_dir, accessioned_index_file))

        # assert files copied to public ftp
        public_ftp_dir = self.get_public_ftp_dir()
        self.assert_file_copied_to_public_ftp(public_ftp_dir, compress_vcf_file)
        self.assert_file_copied_to_public_ftp(public_ftp_dir, index_vcf_file)
        self.assert_file_copied_to_public_ftp(public_ftp_dir, accessioned_vcf_file)
        self.assert_file_copied_to_public_ftp(public_ftp_dir, accessioned_index_file)

        # assert data loaded to mongodb
        self.assert_data_loaded_to_mongodb()

    def assert_file_copied_to_public_ftp(self, public_ftp_dir, file):
        file_path = os.path.join(public_ftp_dir, file)
        run_quiet_command("run copy command to copy from public ftp",
                          f"docker cp {self.container_name}:{file_path} {self.test_run_dir}")
        assert os.path.isfile(os.path.join(self.test_run_dir, file))

    def get_public_ftp_dir(self):
        yaml_content_submission_config = read_file_from_container(self.container_name,
                                                                  os.path.join('/root', '.submission_config.yml'))
        submission_config = yaml.safe_load(yaml_content_submission_config)
        eload_config = Configuration(
            os.path.join(self.test_run_dir, f'ELOAD_{self.eload_number}', f'.ELOAD_{self.eload_number}_config.yml'))

        public_ftp_dir = os.path.join(submission_config['public_ftp_dir'],
                                      eload_config.query('brokering', 'ena', 'PROJECT'))

        return public_ftp_dir

    def assert_data_from_ena_loaded_to_evapro(self):
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            query = ("select project_accession, taxonomy_id from evapro.project_taxonomy "
                     "where project_accession = 'PRJEB105137'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 4530)]
            assert set(results) == set(expected)

            query = ("select eva_submission_id, eva_submission_status_id from evapro.eva_submission "
                     "where eva_submission_id = 1513")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1513, 6)]
            assert set(results) == set(expected)

            query = ("select project_accession, old_ticket_id, eload_id from evapro.project_eva_submission "
                     "where project_accession = 'PRJEB105137'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 1513, 1513)]
            assert set(results) == set(expected)

            query = "select project_accession, alias from evapro.project where project_accession = 'PRJEB105137'"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 'ELOAD_1513')]
            assert set(results) == set(expected)

            query = ("select project_accession, submission_id from evapro.project_ena_submission "
                     "where project_accession = 'PRJEB105137'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 1)]
            assert set(results) == set(expected)

            query = ("select taxonomy_id, common_name, scientific_name, taxonomy_code, eva_name from evapro.taxonomy "
                     "where taxonomy_id=4530")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(4530, 'Asian cultivated rice', 'Oryza sativa', 'osativa', 'Asian cultivated rice')]
            assert set(results) == set(expected)

            query = ("select submission_id, submission_accession, type from evapro.submission "
                     "where submission_accession = 'ERA35393650'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'ERA35393650', 'PROJECT')]
            assert set(results) == set(expected)

            query = ("select assembly_set_id, taxonomy_id, assembly_name, assembly_code from evapro.assembly_set "
                     "where taxonomy_id = 4530")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 4530, 'IRGSP-1.0', 'irgsp10')]
            assert set(results) == set(expected)

            query = ("select assembly_set_id, assembly_accession, assembly_chain, assembly_version from evapro.accessioned_assembly "
                     "where assembly_accession = 'GCA_001433935.1'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'GCA_001433935.1', 'GCA_001433935', 1)]
            assert set(results) == set(expected)

            query = ("select analysis_accession, vcf_reference_accession, assembly_set_id from evapro.analysis "
                     "where analysis_accession = 'ERZ28769990'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 'GCA_001433935.1', 1)]
            assert set(results) == set(expected)

            query = ("select project_accession, analysis_accession from evapro.project_analysis "
                     "where project_accession = 'PRJEB105137'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 'ERZ28769990')]
            assert set(results) == set(expected)

            query = "select experiment_type_id, experiment_type from evapro.experiment_type"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'Whole genome sequencing')]
            assert set(results) == set(expected)

            query = ("select analysis_accession, submission_id from evapro.analysis_submission "
                     "where analysis_accession = 'ERZ28769990'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 1)]
            assert set(results) == set(expected)

            query = ("select analysis_accession, experiment_type_id from evapro.analysis_experiment_type "
                     "where analysis_accession = 'ERZ28769990'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 1)]
            assert set(results) == set(expected)

            query = "select analysis_accession, file_id from evapro.analysis_file where analysis_accession = 'ERZ28769990'"
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('ERZ28769990', 1), ('ERZ28769990', 2)]
            assert set(results) == set(expected)

            query = ("select project_accession, sample_count, pro_samp1_id from evapro.project_samples_temp1 "
                     "where project_accession = 'PRJEB105137'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 0, 43)]
            assert set(results) == set(expected)

            query = ("select project_accession, taxonomy_ids from evapro.project_children_taxonomy "
                     "where project_accession = 'PRJEB105137'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', '4530')]
            assert set(results) == set(expected)

            query = ("select project_accession, reference_accession from evapro.project_reference "
                     "where project_accession = 'PRJEB105137'")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [('PRJEB105137', 'GCA_001433935.1')]
            assert set(results) == set(expected)

            query = ("select sample_id, biosample_accession, ena_accession from evapro.sample "
                     "where biosample_accession in ('SAMD00045866', 'SAMD00045867', 'SAMD00045868', 'SAMD00045869', 'SAMD00045870')")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'SAMD00045866', 'DRS029882'), (2, 'SAMD00045867', 'DRS029883'),
                        (3, 'SAMD00045868', 'DRS029884'), (4, 'SAMD00045869', 'DRS029885'),
                        (5, 'SAMD00045870', 'DRS029886')]
            assert set(results) == set(expected)

            query = ("select file_id, ena_submission_file_id, file_md5, file_type, file_size  from evapro.file "
                     "where ena_submission_file_id in ('ERF219841043','ERF219841044')")
            results = get_all_results_for_query(metadata_connection_handle, query)
            expected = [(1, 'ERF219841043', '77b3f2576319887b36479474c39bf5e6', 'VCF', 50824503470),
                        (2, 'ERF219841044', 'bbca217c4ca11a8068b11fb9fb051a5e', 'CSI', 335146)]
            assert set(results) == set(expected)

    def assert_data_loaded_to_mongodb(self):
        with get_mongo_connection_handle(self.maven_profile, self.maven_settings_file) as mongo_conn:
            variant_database = mongo_conn['eva_spombe_asm294v2']

            files_coll = variant_database["files_2_0"]
            files_coll_total_count = files_coll.count_documents({})
            assert files_coll_total_count == 1
            files_coll_count = files_coll.count_documents(
                {"fid": "ERZ28769990", "fname": "vcf_file_ASM294v2.vcf.gz", "sid": "PRJEB105137"})
            assert files_coll_count == 1

            variant_coll = variant_database["variants_2_0"]
            variant_coll_total_count = variant_coll.count_documents({})
            assert variant_coll_total_count == 4
            variant_coll_count = variant_coll.count_documents(
                {"_id": {"$in": ["CU329670.1_721105_G_T",
                                 "CU329671.1_721105_G_T",
                                 "CU329672.1_721105_T_G",
                                 "X54421.1_3205_A_T"]}})
            assert variant_coll_count == 4

            annotations_coll = variant_database["annotations_2_0"]
            annotations_coll_total_count = annotations_coll.count_documents({})
            assert annotations_coll_total_count == 4
            annotations_coll_count = annotations_coll.count_documents(
                {"_id": {"$in": ["CU329671.1_721105_G_T_115_62",
                                 "X54421.1_3205_A_T_115_62",
                                 "CU329672.1_721105_T_G_115_62",
                                 "CU329670.1_721105_G_T_115_62"]}})
            assert annotations_coll_count == 4

            annotation_metadata_coll = variant_database["annotationMetadata_2_0"]
            annotation_metadata_total_count = annotation_metadata_coll.count_documents({})
            assert annotation_metadata_total_count == 1
            annotation_metadata_count = annotation_metadata_coll.count_documents(
                {"cacheVersion": "62", "vepVersion": "115", "defaultVersion": True})
            assert annotation_metadata_count == 1

            accession_database = mongo_conn["eva_accession_sharded"]
            sve_coll = accession_database['submittedVariantEntity']
            accessioned_variants_count = sve_coll.count_documents(
                {'seq': 'GCA_000002945.2', 'study': 'PRJEB105137', 'tax': 4896})
            assert accessioned_variants_count == 4
