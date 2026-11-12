import json
import os
import re
import subprocess

from ebi_eva_common_pyutils.logger import logging_config as log_cfg
from ebi_eva_internal_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_internal_pyutils.pg_utils import get_all_results_for_query, execute_query

from utils.test_with_docker_compose import TestWithDockerCompose

logger = log_cfg.get_logger(__name__)


def extract_nextflow_work_dirs_from_log(input_file):
    """
    Extract the value following 'work-dir' from a log line containing the nextflow command.
    """
    pattern = re.compile(r"work-dir\s+(\S+)")

    with open(input_file, "r") as f:
        for line in f:
            if "Running command:" in line and "nextflow" in line:
                match = pattern.search(line)
                if match:
                    yield match.group(1)

class TestEvaSubmission(TestWithDockerCompose):
    initialize_submission_account = True
    vcf_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(TestWithDockerCompose.resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(TestWithDockerCompose.resources_directory, 'assembly_reports')

    test_run_dir = os.path.join(TestWithDockerCompose.tests_directory, 'eva_submission_test_run')
    metadata_xlsx = os.path.join(test_run_dir, 'metadata_xlsx.xlsx')
    old_metadata_xlsx = os.path.join(test_run_dir, 'old_metadata_xlsx.xlsx')
    metadata_json = os.path.join(test_run_dir, 'eva_sub_cli_metadata.json')

    docker_compose_file = os.path.join(TestWithDockerCompose.root_dir, 'components',
                                       'docker-compose-eva-submission.yml')
    container_name = 'eva_submission_test'
    container_reference_genome_dir = '/opt/reference_sequences/nitrospira/GCA_000002945.2'
    container_ftp_submission_dir = '/opt/ftp/private/eva-box-01/upload/username'
    container_submission_dir = '/opt/submissions'

    maven_settings_file = os.path.join(TestWithDockerCompose.root_dir, 'components', 'maven-settings.xml')
    maven_profile = 'localhost'

    def setUp(self):
        super().setUp()
        self.container_log_files = []

    def assert_submission_processing_status_updated(self, submission_id, step, status):
        metadata_connection_handle = get_metadata_connection_handle(self.maven_profile, self.maven_settings_file)
        with metadata_connection_handle:
            submission_status_query = (f"SELECT status FROM eva_submissions.submission_processing_status "
                                       f"where submission_id = '{submission_id}' and step = '{step}'")
            results = get_all_results_for_query(metadata_connection_handle, submission_status_query)
            assert len(results) == 1
            assert results[0][0] == status

    def get_submission_id_from_db(self, eload_number):
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            query = (
                f"select submission_id, eload, source from eva_submissions.submission_eload where eload = {eload_number}")
            results = get_all_results_for_query(metadata_connection_handle, query)
            return results[0][0]

    def put_submission_in_db(self, submission_id, eload_number, source_type="email", create_account=True):
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            if create_account:
                query = (
                    f"INSERT INTO eva_submissions.submission_account(id, user_id, login_type, primary_email, first_name, last_name) "
                    f"VALUES('Webin-9999_webin', 'Webin-9999', 'webin', 'user@example.com', 'user', 'user')")
                execute_query(metadata_connection_handle, query)

            query = (
                f" INSERT INTO eva_submissions.submission(submission_id, status, submission_account_id, initiation_time) "
                f"VALUES('{submission_id}', 'OPEN', 'Webin-9999_webin', now())")
            execute_query(metadata_connection_handle, query)

            query = (
                f"INSERT INTO eva_submissions.submission_details(submission_id, project_title, project_description, metadata_json) "
                f"VALUES('{submission_id}', 'Test Project', 'Test Description', '{{}}'::jsonb)")
            execute_query(metadata_connection_handle, query)

            query = (f"insert into eva_submissions.submission_eload (submission_id, eload, source) "
                     f"values ('{submission_id}', {eload_number}, '{source_type}')")
            execute_query(metadata_connection_handle, query)

    def _query_metadata_db(self, query):
        with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
            return get_all_results_for_query(metadata_connection_handle, query)

    def get_tracking_details_from_db(self, submission_id):
        """Submission level tracking details as stored by eva-submission-ws, None if there are none."""
        results = self._query_metadata_db(
            f"SELECT release_date, project_accession, project_title, project_taxonomies, metadata_json_file "
            f"FROM eva_submissions.submission_tracking_details WHERE submission_id = '{submission_id}'"
        )
        assert len(results) <= 1
        if not results:
            return None
        keys = ['release_date', 'project_accession', 'project_title', 'project_taxonomies', 'metadata_json_file']
        return dict(zip(keys, results[0]))

    def get_submitted_analyses_from_db(self, submission_id):
        """Dict of analysis alias to the analysis details stored by eva-submission-ws."""
        results = self._query_metadata_db(
            f"SELECT analysis_alias, analysis_accession, aggregation_type, assembly_accession "
            f"FROM eva_submissions.submitted_analysis WHERE submission_id = '{submission_id}'"
        )
        keys = ['analysis_accession', 'aggregation_type', 'assembly_accession']
        return {row[0]: dict(zip(keys, row[1:])) for row in results}

    def get_submitted_vcfs_from_db(self, submission_id):
        """Dict of (analysis alias, submitted file) to the VCF details stored by eva-submission-ws."""
        results = self._query_metadata_db(
            f"SELECT analysis_alias, submitted_file, brokered_file, csi_file, brokered_file_md5, csi_file_md5 "
            f"FROM eva_submissions.submitted_vcf WHERE submission_id = '{submission_id}'"
        )
        keys = ['brokered_file', 'csi_file', 'brokered_file_md5', 'csi_file_md5']
        return {(row[0], row[1]): dict(zip(keys, row[2:])) for row in results}

    def get_submitted_samples_from_db(self, submission_id):
        """Dict of analysis alias to a dict of sample name to sample accession stored by eva-submission-ws."""
        results = self._query_metadata_db(
            f"SELECT j.analysis_alias, s.sample_name, s.sample_accession "
            f"FROM eva_submissions.submitted_analysis_submitted_sample j "
            f"JOIN eva_submissions.submitted_sample s "
            f"ON s.submission_id = j.sample_submission_id AND s.sample_name = j.sample_name "
            f"WHERE j.analysis_submission_id = '{submission_id}'"
        )
        samples_per_analysis = {}
        for analysis_alias, sample_name, sample_accession in results:
            samples_per_analysis.setdefault(analysis_alias, {})[sample_name] = sample_accession
        return samples_per_analysis

    def assert_preparation_state_stored_in_db(self, submission_id, config):
        """The state written to the config by the preparation is also stored in the database."""
        tracking_details = self.get_tracking_details_from_db(submission_id)
        assert tracking_details is not None, f'No tracking details stored for {submission_id}'
        assert tracking_details['metadata_json_file'] == config.query('submission', 'metadata_json')
        assert tracking_details['project_title'] == config.query('submission', 'project_title')
        taxonomy_id = config.query('submission', 'taxonomy_id')
        assert tracking_details['project_taxonomies'] == (str(taxonomy_id) if taxonomy_id else None)

        analyses_in_config = config.query('submission', 'analyses', ret_default={})
        assert analyses_in_config, 'The preparation should have stored the analyses in the config'
        analyses_in_db = self.get_submitted_analyses_from_db(submission_id)
        vcfs_in_db = self.get_submitted_vcfs_from_db(submission_id)
        assert set(analyses_in_db) == set(analyses_in_config)
        for analysis_alias, analysis_info in analyses_in_config.items():
            assert analyses_in_db[analysis_alias]['assembly_accession'] == analysis_info.get('assembly_accession')
            vcfs_of_analysis = {vcf for alias, vcf in vcfs_in_db if alias == analysis_alias}
            assert vcfs_of_analysis == set(analysis_info.get('vcf_files', []))

    def assert_validation_state_stored_in_db(self, submission_id, config):
        """The evidence/aggregation type found by the validation is also stored in the database."""
        aggregation_types = config.query('validation', 'aggregation_check', 'analyses', ret_default={})
        assert aggregation_types, 'The validation should have stored the aggregation types in the config'
        analyses_in_db = self.get_submitted_analyses_from_db(submission_id)
        for analysis_alias, aggregation_type in aggregation_types.items():
            assert analyses_in_db[analysis_alias]['aggregation_type'] == aggregation_type

    def assert_brokering_state_stored_in_db(self, submission_id, config):
        """The accessions, brokered files and samples written to the config by the brokering are in the database."""
        tracking_details = self.get_tracking_details_from_db(submission_id)
        assert tracking_details is not None, f'No tracking details stored for {submission_id}'
        assert tracking_details['release_date'] is not None
        project_accession = config.query('brokering', 'ena', 'PROJECT')
        assert project_accession.startswith('PRJE')
        assert tracking_details['project_accession'] == project_accession

        analyses_in_db = self.get_submitted_analyses_from_db(submission_id)
        analysis_accessions = config.query('brokering', 'ena', 'ANALYSIS', ret_default={})
        assert analysis_accessions
        for analysis_alias, analysis_accession in analysis_accessions.items():
            assert analysis_accession.startswith('ERZ')
            assert analyses_in_db[analysis_alias]['analysis_accession'] == analysis_accession

        vcfs_in_db = self.get_submitted_vcfs_from_db(submission_id)
        for analysis_alias, analysis_info in config.query('brokering', 'analyses', ret_default={}).items():
            for brokered_file, vcf_info in analysis_info['vcf_files'].items():
                vcf_in_db = vcfs_in_db[(analysis_alias, vcf_info['original_vcf'])]
                assert vcf_in_db['brokered_file'] == brokered_file
                assert vcf_in_db['csi_file'] == vcf_info['csi']
                assert vcf_in_db['brokered_file_md5'] == vcf_info['md5']
                assert vcf_in_db['csi_file_md5'] == vcf_info['csi_md5']

        samples_in_db = self.get_submitted_samples_from_db(submission_id)
        for record in config.query('brokering', 'Biosamples', 'sample_records', ret_default=[]):
            if not record.get('sampleInVCF'):
                continue
            for analysis_alias in record['analysisAlias']:
                unique_alias = analysis_alias if analysis_alias.startswith(submission_id) \
                    else f'{submission_id}_{analysis_alias}'
                assert samples_in_db[unique_alias][record['sampleInVCF']] == record['accession']

    # def seed_tracking_details_in_db(self, submission_id, project_accession, project_taxonomies, analyses,
    #                                 release_date=None):
    #     """
    #     Store tracking details in the database the way eva-submission-ws does, to simulate a submission whose
    #     state was stored in the database. analyses is a list of dict with the keys alias, accession, aggregation and
    #     assembly.
    #     """
    #     release_date_value = f"'{release_date}'" if release_date else 'NULL'
    #     with get_metadata_connection_handle(self.maven_profile, self.maven_settings_file) as metadata_connection_handle:
    #         execute_query(metadata_connection_handle, (
    #             f"INSERT INTO eva_submissions.submission_tracking_details "
    #             f"(submission_id, project_accession, project_taxonomies, release_date) "
    #             f"VALUES ('{submission_id}', '{project_accession}', '{project_taxonomies}', {release_date_value})"
    #         ))
    #         for analysis in analyses:
    #             execute_query(metadata_connection_handle, (
    #                 f"INSERT INTO eva_submissions.submitted_analysis "
    #                 f"(submission_id, analysis_alias, analysis_accession, aggregation_type, assembly_accession) "
    #                 f"VALUES ('{submission_id}', '{analysis['alias']}', '{analysis['accession']}', "
    #                 f"'{analysis['aggregation']}', '{analysis['assembly']}')"
    #             ))
    #             execute_query(metadata_connection_handle, (
    #                 f"INSERT INTO eva_submissions.submission_submitted_analysis (submission_id, analysis_alias) "
    #                 f"VALUES ('{submission_id}', '{analysis['alias']}')"
    #             ))

    def seed_tracking_details_in_db(self, submission_id, project_accession, project_taxonomies, analyses,
                                    release_date=None):
        """
        Store tracking details through eva-submission-ws, as the processing scripts do, to simulate a submission
        whose state was stored in the database. analyses is a list of dict with the keys alias, accession,
        aggregation and assembly.
        """
        body = {
            'projectAccession': project_accession,
            'projectTaxonomies': project_taxonomies,
            'analyses': [{'analysisAlias': a['alias'], 'analysisAccession': a['accession'],
                          'aggregationType': a['aggregation'], 'assemblyAccession': a['assembly']}
                         for a in analyses]
        }
        if release_date:
            body['releaseDate'] = release_date
        self.call_submission_ws_from_container('PUT', submission_id, body)

        logger.info('submitted_analysis rows: %s', self._query_metadata_db(
            "select submission_id, analysis_alias from eva_submissions.submitted_analysis"))
        logger.info('submission_submitted_analysis rows: %s', self._query_metadata_db(
            "select submission_id, analysis_alias from eva_submissions.submission_submitted_analysis"))

        # what the ingestion will read back from the database
        stored = self.call_submission_ws_from_container('GET', submission_id)
        assert stored['projectAccession'] == project_accession
        stored_analyses = {a['analysisAlias']: a for a in stored.get('analyses') or []}
        for analysis in analyses:
            assert stored_analyses[analysis['alias']]['analysisAccession'] == analysis['accession']
            assert stored_analyses[analysis['alias']]['aggregationType'] == analysis['aggregation']

    def call_submission_ws_from_container(self, method, submission_id, body=None):
        """Call the tracking details endpoint of eva-submission-ws from the eva_submission container, like the scripts do."""
        script = (
            "import requests, yaml\n"
            "ws = yaml.safe_load(open('/root/.submission_config.yml'))['submissions']['webservice']\n"
            f"url = ws['url'] + '/admin/submission/{submission_id}/trackingDetails'\n"
            f"response = requests.request('{method}', url, json={body!r}, "
            "auth=(ws['admin_username'], ws['admin_password']))\n"
            "print(response.status_code)\n"
            "print(response.text)\n"
            "response.raise_for_status()\n"
        )
        result = subprocess.run(['docker', 'exec', self.container_name, 'python', '-c', script],
                                capture_output=True, text=True)
        logger.info(f'{method} trackingDetails for {submission_id}: {result.stdout} {result.stderr}')
        assert result.returncode == 0, f'{method} trackingDetails failed: {result.stdout} {result.stderr}'
        status_code, _, response_text = result.stdout.partition('\n')
        return json.loads(response_text) if response_text.strip() else None