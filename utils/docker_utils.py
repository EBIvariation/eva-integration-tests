import os
import shutil
import subprocess
from tempfile import mkdtemp

from ebi_eva_common_pyutils.logger import logging_config

from utils.test_utils import run_quiet_command

logger = logging_config.get_logger(__name__)


def run_docker_cmd(description, command):
    log_file = None
    log_dir = None
    try:
        log_dir = mkdtemp()
        log_file = os.path.join(log_dir, "docker-log")
        command_with_log = f'{command} > {log_file} 2>&1'
        run_quiet_command(description, command_with_log, log_error_stream_to_output=True)
    except subprocess.CalledProcessError as e:
        if log_file:
            output = read_file_from_local(log_file)
            print(f'Command {command} {description} failed:')
            print(output)
        raise e
    finally:
        if os.path.exists(log_dir):
            shutil.rmtree(log_dir)


def build_from_docker_compose(docker_compose_file, docker_path='docker'):
    run_docker_cmd("build all services defined in docker compose file",
                   f"{docker_path} compose -f {docker_compose_file} build")


def stop_and_remove_all_containers_in_docker_compose(docker_compose_file, docker_path='docker'):
    run_docker_cmd("stop and remove all containers present in docker compose file",
                   f"{docker_path} compose -f {docker_compose_file} down")


def start_all_containers_in_docker_compose(docker_compose_file, docker_path='docker'):
    run_docker_cmd("start all containers present in docker compose file",
                   f"{docker_path} compose -f {docker_compose_file} up -d")


def copy_files_to_container(container_name, dir_path, file_path, docker_path='docker'):
    run_docker_cmd(f"Create directory structure for copying files into container",
                   f"{docker_path} exec {container_name} mkdir -p {dir_path}")
    run_docker_cmd(f"Copy file to container",
                   f"{docker_path} cp {file_path} {container_name}:{dir_path}/{os.path.basename(file_path)}")


def copy_files_from_container(container_name, dir_path, local_dir_path, docker_path='docker'):
    run_docker_cmd(f"copy dir from container to local",
                   f"{docker_path} cp {container_name}:{dir_path}/. {local_dir_path}")


def read_file_from_container(container_name, file_path, docker_path='docker'):
    return run_quiet_command("read content of the file from container",
                             f'{docker_path} exec {container_name} cat {file_path}',
                             return_process_output=True)


def read_file_from_local(file_path):
    with open(file_path) as f:
        return f.read()


def run_command_in_container(container_name, command_to_run, docker_path='docker'):
    return run_quiet_command("run command in container",
                             f" {docker_path} exec {container_name} {command_to_run}",
                             return_process_output=True)
