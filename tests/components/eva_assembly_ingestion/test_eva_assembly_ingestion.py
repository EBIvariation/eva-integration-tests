import os
from datetime import datetime

from bson import Int64
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.mongo_utils import get_mongo_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query, execute_query
from pymongo.errors import BulkWriteError

from utils.docker_utils import copy_files_to_container, run_command_in_container
from utils.test_utils import run_quiet_command
from utils.test_with_docker_compose import TestWithDockerCompose, log_on_failure


class TestEvaAssemblyIngestion(TestWithDockerCompose):
    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-assembly-ingestion.yml')
    container_name = 'eva_assembly_ingestion_test'

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_assembly_ingestion_test_run')
    settings_file = os.path.join(TestWithDockerCompose.resources_directory, 'maven-settings.xml')

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
        """Insert supported_assembly_tracker rows needed to test assembly ingestion."""
        with get_metadata_connection_handle('docker', self.settings_file) as conn:
            execute_query(
                conn,
                "INSERT INTO "
                "evapro.supported_assembly_tracker (taxonomy_id,source,assembly_id,current,start_date,end_date) "
                "VALUES (9913,'Ensembl','GCA_000003055.5',false,'2021-01-01','2021-12-22'), "
                "(9913,'Ensembl','GCA_002263795.2',false,'2021-12-22','infinity'), " 
                "(9903,'Ensembl','GCA_002263795.2',false,'2021-01-01','infinity') "
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
        with get_mongo_connection_handle("docker", self.settings_file) as mongo_conn:
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
                        'study': 'PRJEB42513',
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

        # TODO assertions
        # TODO expected new rows in supported assembly tracker
        # "(9903,'Ensembl','GCA_002263795.4',true,'2025-10-23','infinity') "
        # "(9913,'Ensembl','GCA_002263795.4',true,'2025-10-23','infinity'), "

        # TODO expected remapped documents - get from DB

        # Verify all 3 submittedVariantEntity documents are deprecated
        # with get_mongo_connection_handle("docker", self.settings_file) as mongo_conn:
        #     count = mongo_conn['eva_accession_sharded']['submittedVariantEntity'].count_documents(
        #         {'study': self.project_accession, 'seq': self.assembly_accession}
        #     )
        #     assert count == 0
        #     count = mongo_conn['eva_accession_sharded']['submittedVariantOperationEntity'].count_documents(
        #         {'inactiveObjects.study': self.project_accession, 'inactiveObjects.seq': self.assembly_accession}
        #     )
        #     assert count == 3
