import os
import shutil
from unittest import TestCase

from tests.webin.webin_test_user import WebinTestUser
from utils.docker_utils import stop_and_remove_all_containers_in_docker_compose, start_all_containers_in_docker_compose, \
    build_from_docker_compose


class TestEvaSubCli(TestCase):
    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    tests_directory = os.path.join(root_dir, 'tests')
    resources_directory = os.path.join(tests_directory, 'resources')

    vcf_files_dir = os.path.join(resources_directory, 'vcf_files')
    fasta_files_dir = os.path.join(resources_directory, 'fasta_files')
    assembly_reports_dir = os.path.join(resources_directory, 'assembly_reports')

    eva_sub_cli_test_run_dir = os.path.join(tests_directory, 'eva_sub_cli_test_run')
    metadata_json = os.path.join(eva_sub_cli_test_run_dir, 'metadata_json.json')
    metadata_xlsx = os.path.join(eva_sub_cli_test_run_dir, 'metadata_xlsx.xlsx')

    docker_compose_file = os.path.join(root_dir, 'components', 'docker-compose-eva-sub-cli.yml')
    container_name = 'eva_sub_cli_test'
    container_submission_dir = '/opt'

    webin_test_user = WebinTestUser()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # build and setup images/containers present in the docker compose file
        build_from_docker_compose(cls.docker_compose_file)

    def setUp(self):
        # stop and remove containers
        stop_and_remove_all_containers_in_docker_compose(self.docker_compose_file)
        # start containers
        start_all_containers_in_docker_compose(self.docker_compose_file)

        # delete and recreate the test run dir
        if os.path.exists(self.eva_sub_cli_test_run_dir):
            shutil.rmtree(self.eva_sub_cli_test_run_dir)
        os.makedirs(self.eva_sub_cli_test_run_dir, exist_ok=True)

        # copy all required file into container
        self.create_submission_dir_and_copy_files_to_container()

    def tearDown(self):
        # delete test run directory
        if os.path.exists(self.eva_sub_cli_test_run_dir):
            shutil.rmtree(self.eva_sub_cli_test_run_dir)

        # stop and remove container
        stop_and_remove_all_containers_in_docker_compose(self.docker_compose_file)

    def get_validation_json_metadata_existing_project(self):
        json_metadata = self.get_validation_json_metadata()
        json_metadata['project'] = {'projectAccession': 'PRJEB12770'}
        return json_metadata

    def get_validation_json_metadata_with_non_vcf_file(self):
        json_metadata = self.get_validation_json_metadata()
        json_metadata['files'].append({
            "analysisAlias": "AA",
            "fileName": "input_passed.vcf.gz.tbi"
        })
        return json_metadata

    def get_validation_json_metadata(self):
        return {
            "submitterDetails": [
                {
                    "firstName": "test_user_first_name",
                    "lastName": "test_user_last_name",
                    "email": "test_user_email@abc.com",
                    "laboratory": "test_user_laboratory",
                    "centre": "test_user_centre"
                }
            ],
            "project": {
                "title": "test_project_title",
                "description": "test_project_description",
                "taxId": 1234,
                "centre": "test_project_centre"
            },
            "analysis": [
                {
                    "analysisTitle": "test_analysis_title",
                    "analysisAlias": "AA",
                    "description": "test_analysis_description",
                    "experimentType": "Whole genome sequencing",
                    "referenceGenome": "test_analysis_reference_genome",
                    "referenceFasta": "input_passed.fa",
                    "assemblyReport": "input_passed.txt"
                }
            ],
            "sample": [
                {
                    "analysisAlias": ["AA"],
                    "sampleInVCF": "HG00096",
                    "bioSampleAccession": "SAME123"
                }
            ],
            "files": [
                {
                    "analysisAlias": "AA",
                    "fileName": "input_passed.vcf"
                }
            ]
        }
