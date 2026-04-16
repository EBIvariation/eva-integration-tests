import os
from datetime import datetime

from bson import Int64
from ebi_eva_common_pyutils.contig_alias.contig_alias import ContigAliasClient
from ebi_eva_internal_pyutils.config_utils import get_contig_alias_db_creds_for_profile
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.mongo_utils import get_mongo_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query, execute_query
from pymongo.errors import BulkWriteError

from utils.docker_utils import copy_files_to_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose, log_on_failure


class TestEvaAssemblyIngestion(TestWithDockerCompose):
    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-assembly-ingestion.yml')
    container_name = 'eva_assembly_ingestion_test'

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_assembly_ingestion_test_run')
    maven_settings_file = os.path.join(TestWithDockerCompose.root_dir, 'components', 'maven-settings.xml')
    maven_profile = 'localhost'

    fasta_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(TestWithDockerCompose.resources_directory, 'assembly_reports')
    container_reference_genome_dir = '/opt/reference_sequences/bos_taurus'

    taxonomy = 9913
    target_assembly = 'GCA_002263795.4'
    release_version = 7

    def setUp(self):
        super().setUp()
        self._prepare_files()
        self._seed_evapro()
        self._seed_mongodb()
        self.container_log_files = []

    def _prepare_files(self):
        # Prepare reference genomes
        copy_files_to_container(self.container_name,
                                os.path.join(self.container_reference_genome_dir, 'GCA_000003055.5'),
                                os.path.join(self.assembly_reports_dir, 'GCA_000003055.5_assembly_report.txt'))
        copy_files_to_container(self.container_name,
                                os.path.join(self.container_reference_genome_dir, 'GCA_000003055.5'),
                                os.path.join(self.fasta_files_dir, 'GCA_000003055.5.fa'))
        copy_files_to_container(self.container_name,
                                os.path.join(self.container_reference_genome_dir, 'GCA_002263795.2'),
                                os.path.join(self.assembly_reports_dir, 'GCA_002263795.2_assembly_report.txt'))
        copy_files_to_container(self.container_name,
                                os.path.join(self.container_reference_genome_dir, 'GCA_002263795.2'),
                                os.path.join(self.fasta_files_dir, 'GCA_002263795.2.fa'))
        copy_files_to_container(self.container_name,
                                os.path.join(self.container_reference_genome_dir, 'GCA_002263795.4'),
                                os.path.join(self.assembly_reports_dir, 'GCA_002263795.4_assembly_report.txt'))
        copy_files_to_container(self.container_name,
                                os.path.join(self.container_reference_genome_dir, 'GCA_002263795.4'),
                                os.path.join(self.fasta_files_dir, 'GCA_002263795.4.fa'))

    def _seed_evapro(self):
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as conn:
            # Supported assembly tracker
            execute_query(
                conn,
                "INSERT INTO evapro.supported_assembly_tracker "
                "(taxonomy_id,source,assembly_id,current,start_date,end_date) "
                "VALUES (9913,'Ensembl','GCA_000003055.5',false,'2021-01-01','2021-12-22'), "
                "(9913,'Ensembl','GCA_002263795.2',true,'2021-12-22','infinity'), "
                "(9903,'Ensembl','GCA_002263795.2',true,'2021-01-01','infinity') "
                "ON CONFLICT DO NOTHING"
            )

            # Minimal metadata for getting source assemblies and taxonomies
            # Projects used in test accessioning data:
            # - (PRJEB29734, 9913, GCA_000003055.5)
            # - (PRJEB42513, 9913, GCA_002263795.2)
            # - (PRJEB42510, 9903, GCA_002263795.2)
            # - (PRJEB30734, 9913, GCA_002263795.4)  <-- This is the target assembly
            execute_query(conn,
                          "INSERT INTO evapro.project "
                          "(project_accession, center_name, alias, title, description, scope, material, type, "
                          "ena_status, eva_status) "
                          "VALUES ('PRJEB29734', 'Test Centre', 'ELOAD_1', 'Test Study', 'Test description', "
                          "'Multi-isolate', 'DNA', 'Study', 4, 1), "
                          "('PRJEB42513', 'Test Centre', 'ELOAD_2', 'Test Study', 'Test description', "
                          "'Multi-isolate', 'DNA', 'Study', 4, 1), "
                          "('PRJEB42510', 'Test Centre', 'ELOAD_3', 'Test Study', 'Test description', "
                          "'Multi-isolate', 'DNA', 'Study', 4, 1), "
                          "('PRJEB30734', 'Test Centre', 'ELOAD_4', 'Test Study', 'Test description', "
                          "'Multi-isolate', 'DNA', 'Study', 4, 1)"
                          "ON CONFLICT DO NOTHING"
                          )
            execute_query(conn,
                          "INSERT INTO evapro.taxonomy (taxonomy_id, common_name, scientific_name, taxonomy_code, eva_name) "
                          "VALUES (9913, 'Cattle', 'Bos taurus', 'btaurus', 'cow'), "
                          "(9903, 'Oxen cattle', 'Bos', 'bos', 'cattle')"
                          "ON CONFLICT DO NOTHING"
                          )
            execute_query(conn,
                          "INSERT INTO evapro.project_taxonomy (project_accession, taxonomy_id) "
                          "VALUES ('PRJEB29734', 9913), ('PRJEB42513', 9913), ('PRJEB42510', 9903), "
                          "('PRJEB30734', 9913) "
                          "ON CONFLICT DO NOTHING"
                          )
            execute_query(conn,
                          "INSERT INTO evapro.assembly_set (taxonomy_id, assembly_name, assembly_code) "
                          "VALUES (9913, 'Bos_taurus_UMD_3.1.1', 'umd311'), "
                          "(9913, 'ARS-UCD1.2', 'arsucd12'), "
                          "(9903, 'ARS-UCD1.2', 'arsucd12'), "
                          "(9913, 'ARS-UCD2.0', 'arsucd20') "
                          "ON CONFLICT DO NOTHING"
                          )
            execute_query(conn,
                          "INSERT INTO evapro.accessioned_assembly (assembly_set_id, assembly_accession, assembly_chain, assembly_version) "
                          "VALUES (1, 'GCA_000003055.5', 'GCA_000003055', 5), "
                          "(2, 'GCA_002263795.2', 'GCA_002263795', 2), "
                          "(3, 'GCA_002263795.2', 'GCA_002263795', 2), "
                          "(4, 'GCA_002263795.4', 'GCA_002263795', 4) "
                          "ON CONFLICT DO NOTHING"
                          )
            execute_query(conn,
                          "INSERT INTO evapro.analysis "
                          "(analysis_accession, title, alias, vcf_reference_accession, hidden_in_eva, assembly_set_id) "
                          "VALUES ('ERZ123', 'Test Analysis', 'test_analysis', 'GCA_000003055.5', 0, 1), "
                          "('ERZ456', 'Test Analysis', 'test_analysis', 'GCA_002263795.2', 0, 2), "
                          "('ERZ789', 'Test Analysis', 'test_analysis', 'GCA_002263795.2', 0, 3), "
                          "('ERZ1011', 'Test Analysis', 'test_analysis', 'GCA_002263795.4', 0, 4) "
                          "ON CONFLICT DO NOTHING"
                          )
            execute_query(conn,
                          "INSERT INTO evapro.project_analysis (project_accession, analysis_accession) "
                          "VALUES ('PRJEB29734', 'ERZ123'), ('PRJEB42513', 'ERZ456'), ('PRJEB42510', 'ERZ789'), "
                          "('PRJEB30734', 'ERZ1011') "
                          "ON CONFLICT DO NOTHING"
                          )
            # dbSNP source assemblies come from release 3 in tracker
            execute_query(conn,
                          "INSERT INTO eva_progress_tracker.remapping_tracker "
                          "(source,taxonomy,scientific_name,origin_assembly_accession,num_studies,num_ss_ids,release_version,assembly_accession,remapping_status) "
                          "VALUES ('DBSNP',9913,'Bos taurus','GCA_000003055.5',1,1,3,'GCA_002263795.2','Completed') "
                          "ON CONFLICT DO NOTHING"
                          )

    @staticmethod
    def _insert_many_ignore_duplicates(collection, documents):
        """Insert documents into a collection, ignoring duplicate key errors."""
        try:
            collection.insert_many(documents, ordered=False)
        except BulkWriteError as e:
            if any(err['code'] != 11000 for err in e.details.get('writeErrors', [])):
                raise

    def _seed_mongodb(self):
        """Insert MongoDB documents needed for testing assembly ingestion."""
        with get_mongo_connection_handle(self.maven_profile, self.maven_settings_file) as mongo_conn:
            # EVA variants:
            # - (9913, GCA_000003055.5) - 1 native SVE, no CVE
            # - (9913, GCA_002263795.2) - 1 remapped SVE, 1 native SVE, 2 CVEs
            # - (9903, GCA_002263795.2) - 1 native SVE, 1 CVE
            self._insert_many_ignore_duplicates(
                mongo_conn['eva_accession_sharded']['submittedVariantEntity'],
                [
                    {
                        '_id': '07BD7895F39027F967A410EDDA24888EEDBFC558',
                        'seq': 'GCA_000003055.5',
                        'tax': 9913,
                        'study': 'PRJEB29734',
                        'contig': 'GK000025.2',
                        'start': Int64(30053788),
                        'ref': 'A',
                        'alt': 'G',
                        'accession': Int64(5318084591),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2019-07-08T07:30:46.352Z"),
                        'backPropRS': Int64(3000002148)
                    },
                    {
                        '_id': '449E383DD8BC0E36EA75512B7C511A93B1A443A3',
                        'seq': 'GCA_002263795.2',
                        'tax': 9913,
                        'study': 'PRJEB29734',
                        'contig': 'CM008192.2',
                        'start': Int64(29792264),
                        'ref': 'A',
                        'alt': 'G',
                        'remappedFrom': 'GCA_000003055.5',
                        'remappedDate': datetime.fromisoformat("2021-08-12T01:55:28.328Z"),
                        'remappingId': '778BEEA595920286BA9CC9ECF13442A69F9DA73B',
                        'accession': Int64(5318084591),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2019-07-08T07:30:46.352Z"),
                        'rs': Int64(3000002148)
                    },
                    {
                        '_id': 'CC89CFDEBA5E17F392963B839BCDE4A105A4D9B0',
                        'seq': 'GCA_002263795.2',
                        'tax': 9913,
                        'study': 'PRJEB42513',
                        'contig': 'CM008192.2',
                        'start': Int64(3059780),
                        'ref': 'T',
                        'alt': 'C',
                        'accession': Int64(7297377828),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2021-01-19T10:10:51.482Z"),
                        'rs': Int64(3000001769)
                    },
                    {
                        '_id': 'DEBE9A053C76D33EE59CE35760AFF029A1354A8B',
                        'seq': 'GCA_002263795.2',
                        'tax': 9903,
                        'study': 'PRJEB42510',
                        'contig': 'CM008192.2',
                        'start': Int64(242863),
                        'ref': 'A',
                        'alt': 'G',
                        'accession': Int64(7297377658),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2021-01-19T10:10:50.811Z"),
                        'rs': Int64(3000003639)
                    }
                ]
            )
            self._insert_many_ignore_duplicates(
                mongo_conn['eva_accession_sharded']['clusteredVariantEntity'],
                [
                    {
                        '_id': '5796A78BDC9689085FB40D59A062CDE863418EF6',
                        'asm': 'GCA_002263795.2',
                        'tax': 9913,
                        'contig': 'CM008192.2',
                        'start': Int64(29792264),
                        'type': 'SNV',
                        'accession': Int64(3000002148),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2021-12-12T05:23:02.670Z")
                    },
                    {
                        '_id': '63BCE4B3D08D2DC4507C5593DE8AE50F9BEE5DDD',
                        'asm': 'GCA_002263795.2',
                        'tax': 9913,
                        'contig': 'CM008192.2',
                        'start': Int64(3059780),
                        'type': 'SNV',
                        'accession': Int64(3000001769),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2021-12-11T19:54:08.754Z")
                    },
                    {
                        '_id': '0F068D7688A936BB7104C8167613E4BD7AF8A2E0',
                        'asm': 'GCA_002263795.2',
                        'tax': 9913,
                        'contig': 'CM008192.2',
                        'start': Int64(242863),
                        'type': 'SNV',
                        'accession': Int64(3000003639),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2021-12-11T20:38:17.067Z")
                    }
                ]
            )

            # dbSNP variants:
            # - (9913, GCA_000003055.5) - 1 native SVE, 1 CVE
            self._insert_many_ignore_duplicates(
                mongo_conn['eva_accession_sharded']['dbsnpSubmittedVariantEntity'],
                [
                    {
                        '_id': 'FF8DA009964D6392A083972FA9B256D80AFAC7F7',
                        'seq': 'GCA_000003055.5',
                        'tax': 9913,
                        'study': 'BIOPOP_WHOLE_GENOME_SNP_ASSAY',
                        'contig': 'GK000025.2',
                        'start': Int64(4899413),
                        'ref': 'G',
                        'alt': 'A',
                        'rs': Int64(29026047),
                        'evidence': False,
                        'accession': Int64(2116748425),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2016-10-16T00:00:00.000Z")
                    }
                ]
            )
            self._insert_many_ignore_duplicates(
                mongo_conn['eva_accession_sharded']['dbsnpClusteredVariantEntity'],
                [
                    {
                        '_id': 'F0319CC831D4E1F237E9003D1BEE7C399A90CEC8',
                        'asm': 'GCA_000003055.5',
                        'tax': 9913,
                        'contig': 'GK000025.2',
                        'start': Int64(4899413),
                        'type': 'SNV',
                        'validated': True,
                        'accession': Int64(29026047),
                        'version': 1,
                        'createdDate': datetime.fromisoformat("2005-07-13T11:00:00.000Z")
                    }
                ]
            )

    @log_on_failure
    def test_assembly_ingestion(self):
        log_file = 'ingest_assembly.log'
        self.container_log_files.append((self.container_name, log_file))
        cmd = (
            f"docker exec {self.container_name} sh -c "
            f"'add_target_assembly.py "
            f"--taxonomy {self.taxonomy} "
            f"--target_assembly {self.target_assembly} "
            f"--release_version {self.release_version} "
            f"> {log_file} 2>&1'"
        )
        run_quiet_command('run add_target_assembly.py', cmd)

        associated_taxonomy = 9903
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as conn:
            # Supported assembly should be updated for both taxonomies
            supported_assembly_query = (
                f"SELECT assembly_id FROM evapro.supported_assembly_tracker "
                f"WHERE taxonomy_id in ({self.taxonomy}, {associated_taxonomy}) "
                f"AND current = 'true'"
            )
            results = get_all_results_for_query(conn, supported_assembly_query)
            assert len(results) == 2
            for result in results:
                assert result[0] == self.target_assembly

            # Remapping tracker should contain 5 completed jobs:
            # - 1 source assembly for dbSNP
            # - 2 source assemblies for EVA (Bos Taurus)
            # - 1 source assemblies for EVA (Bos)
            # - 1 source assemblies for EVA that is also the target assembly
            remapping_tracker_query = (
                f"SELECT remapping_status FROM eva_progress_tracker.remapping_tracker "
                f"WHERE release_version={self.release_version} "
                f"AND assembly_accession='{self.target_assembly}'"
            )
            results = get_all_results_for_query(conn, remapping_tracker_query)
            assert len(results) == 5
            for result in results:
                assert result[0] == 'Completed'

            clustered_variant_update_query = (
                f"SELECT source FROM evapro.clustered_variant_update "
                f"WHERE assembly_accession='{self.target_assembly}'"
                f"AND taxonomy_id='{self.taxonomy}'"

            )
            results = get_all_results_for_query(conn, clustered_variant_update_query)
            assert len(results) == 3
            assert ['GCA_000003055.5', 'GCA_002263795.2', 'GCA_002263795.4'] == sorted([row[0] for row in results])

            clustered_variant_update_query = (
                f"SELECT source FROM evapro.clustered_variant_update "
                f"WHERE assembly_accession='{self.target_assembly}'"
                f"AND taxonomy_id='{associated_taxonomy}'"

            )
            results = get_all_results_for_query(conn, clustered_variant_update_query)
            assert len(results) == 1
            assert ['GCA_002263795.2'] == sorted([row[0] for row in results])

        # Contig alias should contain the new assembly
        contig_alias_client = ContigAliasClient(get_contig_alias_db_creds_for_profile(self.maven_profile, self.maven_settings_file)[0])
        assembly = contig_alias_client.assembly(self.target_assembly)
        assert assembly is not None

        with get_mongo_connection_handle(self.maven_profile, self.maven_settings_file) as mongo_conn:
            # 3 remapped SVEs and CVEs for EVA
            assert mongo_conn['eva_accession_sharded']['submittedVariantEntity'].count_documents(
                {'seq': self.target_assembly}
            ) == 3
            assert mongo_conn['eva_accession_sharded']['clusteredVariantEntity'].count_documents(
                {'asm': self.target_assembly}
            ) == 3

            # 1 remapped SVE and CVE for dbSNP
            assert mongo_conn['eva_accession_sharded']['dbsnpSubmittedVariantEntity'].count_documents(
                {'seq': self.target_assembly}
            ) == 1
            assert mongo_conn['eva_accession_sharded']['dbsnpClusteredVariantEntity'].count_documents(
                {'asm': self.target_assembly}
            ) == 1
