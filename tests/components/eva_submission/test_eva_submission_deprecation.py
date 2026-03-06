import os
from datetime import datetime, timezone

from bson import Int64
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.mongo_utils import get_mongo_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query, execute_query
from pymongo.errors import BulkWriteError

from utils.docker_utils import copy_files_to_container, run_command_in_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose, log_on_failure


class TestEvaSubmissionDeprecation(TestWithDockerCompose):
    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-submission.yml')
    container_name = 'eva_submission_test'
    mongo_container_name = 'mongo_db_test'
    container_eload_dir = '/opt/submissions'
    container_output_dir = '/opt/deprecation_output'

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_deprecation_test_run')
    settings_file = os.path.join(TestWithDockerCompose.resources_directory, 'maven-settings.xml')

    project_accession = 'PRJEB12345'
    eload_id = 1
    assembly_accession = 'GCA_000004515.4'
    taxonomy_id = 3847

    # Accession report path inside the container
    container_accession_report = '/opt/submissions/ELOAD_1/60_eva_public/test_sample.accessioned.vcf.gz'

    def setUp(self):
        super().setUp()
        self._seed_evapro()
        self._seed_mongodb()
        self._create_accession_report()
        self.container_log_files = []
        run_command_in_container(self.container_name, f'mkdir -p {self.container_output_dir}')

    def _seed_evapro(self):
        """Insert the minimal EVAPRO rows needed to deprecate PRJEB12345."""
        with get_metadata_connection_handle('docker', self.settings_file) as conn:
            execute_query(conn,
                "INSERT INTO evapro.taxonomy (taxonomy_id, common_name, scientific_name, taxonomy_code, eva_name) "
                "VALUES (3847, 'Soybean', 'Glycine max', 'gmax', 'Soybean') "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.assembly_set (taxonomy_id, assembly_name, assembly_code) "
                "VALUES (3847, 'Glycine_max_v2.0', 'glycine_max_v2') "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.accessioned_assembly "
                "(assembly_set_id, assembly_accession, assembly_chain, assembly_version) "
                "SELECT assembly_set_id, 'GCA_000004515.4', 'GCA_000004515', 4 "
                "FROM evapro.assembly_set WHERE assembly_code = 'glycine_max_v2' "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.eva_submission (eva_submission_id, eva_submission_status_id) "
                "VALUES (1, 6) "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.project "
                "(project_accession, center_name, alias, title, description, scope, material, type, "
                "ena_status, eva_status) "
                "VALUES ('PRJEB12345', 'Test Centre', 'ELOAD_1', 'Test Study', 'Test description', "
                "'Multi-isolate', 'DNA', 'Study', 4, 1) "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.project_taxonomy (project_accession, taxonomy_id) "
                "VALUES ('PRJEB12345', 3847) "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.analysis "
                "(analysis_accession, title, alias, vcf_reference_accession, hidden_in_eva, assembly_set_id) "
                "SELECT 'ERZ99999', 'Test Analysis', 'test_analysis', 'GCA_000004515.4', 0, assembly_set_id "
                "FROM evapro.assembly_set WHERE assembly_code = 'glycine_max_v2' "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.project_analysis (project_accession, analysis_accession) "
                "VALUES ('PRJEB12345', 'ERZ99999') "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.project_eva_submission (project_accession, old_ticket_id, eload_id) "
                "VALUES ('PRJEB12345', 1, 1) "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn,
                "INSERT INTO evapro.file "
                "(filename, file_md5, file_type, file_class, file_version, is_current) "
                "VALUES ('test_sample.vcf.gz', 'abc123', 'VCF', 'submitted', 1, 1)"
            )
            execute_query(conn,
                "INSERT INTO evapro.analysis_file (analysis_accession, file_id) "
                "SELECT 'ERZ99999', file_id FROM evapro.file WHERE filename = 'test_sample.vcf.gz' "
                "ON CONFLICT DO NOTHING"
            )
            execute_query(conn, "REFRESH MATERIALIZED VIEW evapro.study_browser")

    @staticmethod
    def _insert_many_ignore_duplicates(collection, documents):
        """Insert documents into a collection, ignoring duplicate key errors."""
        try:
            collection.insert_many(documents, ordered=False)
        except BulkWriteError as e:
            if any(err['code'] != 11000 for err in e.details.get('writeErrors', [])):
                raise

    def _seed_mongodb(self):
        """Insert MongoDB documents needed by deprecation tests."""
        created_date = datetime(2021, 4, 28, 16, 32, 11, 168000, tzinfo=timezone.utc)
        with get_mongo_connection_handle("docker", self.settings_file) as mongo_conn:
            # mongo_conn.admin.command({"enableSharding": 'eva_accession_sharded'})
            # mongo_conn.admin.command({'shardCollection': 'eva_accession_sharded.submittedVariantEntity', 'key':{'_id': 1}})
            self._insert_many_ignore_duplicates(
                mongo_conn['eva_accession_sharded']['submittedVariantEntity'],
                [
                    {
                        '_id': 'A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2',
                        'seq': 'GCA_000004515.4', 'tax': 3847, 'study': 'PRJEB12345',
                        'contig': 'CM000834.3', 'start': Int64(315),
                        'ref': 'G', 'alt': 'C',
                        'accession': Int64(100000001), 'version': 1, 'createdDate': created_date
                    },
                    {
                        '_id': 'B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3',
                        'seq': 'GCA_000004515.4', 'tax': 3847, 'study': 'PRJEB12345',
                        'contig': 'CM000834.3', 'start': Int64(420),
                        'ref': 'A', 'alt': 'T',
                        'accession': Int64(100000002), 'version': 1, 'createdDate': created_date
                    },
                    {
                        '_id': 'C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4',
                        'seq': 'GCA_000004515.4', 'tax': 3847, 'study': 'PRJEB12345',
                        'contig': 'CM000834.3', 'start': Int64(530),
                        'ref': 'T', 'alt': 'C',
                        'accession': Int64(100000003), 'version': 1, 'createdDate': created_date
                    },
                ]
            )
            # mongo_conn.admin.command({"enableSharding": 'eva_glycine_max_v2'})
            # mongo_conn.admin.command({'shardCollection': 'eva_glycine_max_v2.variants_2_0', 'key':{'chr': 1, 'start': 1}})
            variant_db = mongo_conn['eva_glycine_max_v2']
            self._insert_many_ignore_duplicates(
                variant_db['variants_2_0'],
                [
                    {
                        '_id': 'CM000834.3_315_G_C',
                        'chr': 'CM000834.3', 'start': 315,
                        '_at': {'chunkIds': ['CM000834.3_0_1k', 'CM000834.3_0_10k']},
                        'alt': 'C', 'end': 315,
                        'files': [{
                            'fid': 'ERZ99999', 'sid': 'PRJEB12345',
                            'attrs': {'QUAL': '100', 'AC': '1', 'AF': '0.5', 'AN': '2'},
                            'fm': 'GT', 'samp': {'def': '0/1'}
                        }],
                        'hgvs': [{'type': 'genomic', 'name': 'CM000834.3:g.315G>C'}],
                        'len': 1, 'ref': 'G', 'type': 'SNV', 'annot': []
                    },
                    {
                        '_id': 'CM000834.3_420_A_T',
                        'chr': 'CM000834.3', 'start': 420,
                        '_at': {'chunkIds': ['CM000834.3_0_1k', 'CM000834.3_0_10k']},
                        'alt': 'T', 'end': 420,
                        'files': [{
                            'fid': 'ERZ99999', 'sid': 'PRJEB12345',
                            'attrs': {'QUAL': '100', 'AC': '1', 'AF': '0.5', 'AN': '2'},
                            'fm': 'GT', 'samp': {'def': '0/1'}
                        }],
                        'hgvs': [{'type': 'genomic', 'name': 'CM000834.3:g.420A>T'}],
                        'len': 1, 'ref': 'A', 'type': 'SNV', 'annot': []
                    },
                ]
            )
            self._insert_many_ignore_duplicates(
                variant_db['files_2_0'],
                [{'sid': 'PRJEB12345', 'fid': 'ERZ99999', 'fname': 'test_sample.vcf.gz'}]
            )

    def _create_accession_report(self):
        """Write a minimal accessioned VCF to test_run_dir, copy to container, bgzip."""
        local_vcf = os.path.join(self.test_run_dir, 'test_sample.accessioned.vcf')
        with open(local_vcf, 'w') as f:
            f.write('##fileformat=VCFv4.1\n')
            f.write('##reference=GCA_000004515.4\n')
            f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n')
            f.write('CM000834.3\t315\tss100000001\tG\tC\t100\tPASS\t.\n')
            f.write('CM000834.3\t420\tss100000002\tA\tT\t100\tPASS\t.\n')
            f.write('CM000834.3\t530\tss100000003\tT\tC\t100\tPASS\t.\n')

        container_dir = '/opt/submissions/ELOAD_1/60_eva_public'
        copy_files_to_container(self.container_name, container_dir, local_vcf)
        container_vcf = f'{container_dir}/test_sample.accessioned.vcf'
        run_command_in_container(self.container_name, f'bgzip -f {container_vcf}')

    def _run_deprecate(self, tasks, extra_args=''):
        """Run deprecate_study.py inside the eva_submission container."""
        log_file = f'{self.container_output_dir}/deprecation.log'
        self.container_log_files.append((self.container_name, log_file))
        cmd = (
            f"docker exec {self.container_name} sh -c "
            f"'deprecate_study.py "
            f"--project_accession {self.project_accession} "
            f"--deprecation_suffix {self.project_accession}_OBSOLETE "
            f"--deprecation_reason \"Withdrawn at submitter request\" "
            f"--output_dir {self.container_output_dir} "
            f"--tasks {tasks} "
            f"{extra_args} "
            f"> {log_file} 2>&1'"
        )
        run_quiet_command('run deprecate_study.py', cmd)

    @log_on_failure
    def test_deprecate_mark_inactive(self):
        self._run_deprecate('mark_inactive')

        with get_metadata_connection_handle('docker', self.settings_file) as conn:
            # project.eva_status should be 0 (inactive)
            results = get_all_results_for_query(
                conn, "SELECT eva_status FROM evapro.project WHERE project_accession = 'PRJEB12345'"
            )
            assert results == [(0,)], f"Expected eva_status=0, got {results}"

            # all linked analyses should have hidden_in_eva = 1
            results = get_all_results_for_query(
                conn,
                "SELECT hidden_in_eva FROM evapro.analysis a "
                "JOIN evapro.project_analysis pa USING (analysis_accession) "
                "WHERE pa.project_accession = 'PRJEB12345'"
            )
            assert all(r[0] == 1 for r in results), \
                f"Expected all analyses hidden_in_eva=1, got {results}"

            # study_browser should no longer contain PRJEB12345 (eva_status=0 excluded)
            results = get_all_results_for_query(
                conn,
                "SELECT project_accession FROM evapro.study_browser "
                "WHERE project_accession = 'PRJEB12345'"
            )
            assert results == [], \
                f"Expected PRJEB12345 absent from study_browser, got {results}"

    @log_on_failure
    def test_deprecate_variants(self):
        deprecation_log_file  = (f'{self.container_output_dir}/'
                                 f'deprecate.{self.container_accession_report}_{self.assembly_accession}.log')
        self.container_log_files.append((self.container_name, deprecation_log_file))
        assemblies_arg = (
            f'--assemblies_accession_reports '
            f'{self.assembly_accession}={self.container_accession_report}'
        )
        self._run_deprecate('deprecate_variants', extra_args=assemblies_arg)

        # Verify via mongosh that all 3 submittedVariantEntity documents are deprecated
        result = run_command_in_container(
            self.mongo_container_name,
            (
                "mongosh --quiet eva_glycine_max_v2 --eval "
                "\"db.submittedVariantEntity.countDocuments({study: 'PRJEB12345', accessioningStopped: true})\""
            )
        )
        assert result is not None and result.strip() == '3', \
            f"Expected 3 deprecated submittedVariantEntity documents, got: {result}"

    @log_on_failure
    def test_deprecate_drop_study(self):
        db_name = 'eva_glycine_max_v2'
        drop_study_log_file = (f'{self.container_output_dir}/'
                                f'drop_study.{db_name}_{self.project_accession}.log')
        self.container_log_files.append((self.container_name, drop_study_log_file))
        assemblies_arg = (
            f'--assemblies_accession_reports '
            f'{self.assembly_accession}={self.container_accession_report}'
        )
        self._run_deprecate('drop_study', extra_args=assemblies_arg)

        # Verify variants_2_0 no longer has PRJEB12345 (study ID is nested in files[].sid)
        variants_count = run_command_in_container(
            self.mongo_container_name,
            (
                f"mongosh --quiet {db_name} --eval "
                "\"db.variants_2_0.countDocuments({'files.sid': 'PRJEB12345'})\""
            )
        )
        assert variants_count is not None and variants_count.strip() == '0', \
            f"Expected 0 variants for PRJEB12345 in variants_2_0, got: {variants_count}"

        # Verify files_2_0 no longer has PRJEB12345
        files_count = run_command_in_container(
            self.mongo_container_name,
            (
                f"mongosh --quiet {db_name} --eval "
                "\"db.files_2_0.countDocuments({sid: 'PRJEB12345'})\""
            )
        )
        assert files_count is not None and files_count.strip() == '0', \
            f"Expected 0 files for PRJEB12345 in files_2_0, got: {files_count}"
