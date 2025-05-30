import csv
import logging

from ebi_eva_common_pyutils.command_utils import run_command_with_output


def create_mapping_file(mapping_file, vcf_files, fasta_files, assembly_reports):
    with open(mapping_file, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(['vcf', 'fasta', 'report'])
        for vcf_file, fasta_file, assembly_reports in zip(vcf_files, fasta_files, assembly_reports):
            writer.writerow([vcf_file, fasta_file, assembly_reports])


def touch(file_path, content=''):
    with open(file_path, 'w') as open_file:
        open_file.write(content)


def run_quiet_command(command_description, command, **kwargs):
    return run_command_with_output(command_description, command, stdout_log_level=logging.DEBUG,
                                   stderr_log_level=logging.DEBUG, **kwargs)
