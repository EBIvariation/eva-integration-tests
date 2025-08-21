import os
import re

from ebi_eva_common_pyutils.logger import logging_config

from utils.test_utils import run_quiet_command

logger = logging_config.get_logger(__name__)


def build_from_docker_compose(docker_compose_file, docker_path='docker'):
    run_quiet_command(
        "build all services defined in docker compose file",
        f"{docker_path} compose -f {docker_compose_file} build",
        log_error_stream_to_output=True
    )


def build_service_from_docker_compose(docker_compose_file, service_name, docker_path='docker'):
    run_quiet_command(
        "build the given service from docker compose file",
        f"{docker_path} compose -f {docker_compose_file} build {service_name}",
        log_error_stream_to_output=True
    )


def build_from_docker_file(image_name, docker_file_path, docker_path='docker', image_tag='latest',
                           docker_build_context='.'):
    run_quiet_command(
        "build image using Dockerfile",
        f"{docker_path} build -t {image_name}:{image_tag} -f {docker_file_path} {docker_build_context}",
        log_error_stream_to_output=True
    )


def stop_and_remove_all_containers_in_docker_compose(docker_compose_file, docker_path='docker'):
    run_quiet_command("stop and remove all containers present in docker compose file",
                      f"{docker_path} compose -f {docker_compose_file} down",
                      log_error_stream_to_output=True
                      )


def start_all_containers_in_docker_compose(docker_compose_file, docker_path='docker'):
    run_quiet_command("start all containers present in docker compose file",
                      f"{docker_path} compose -f {docker_compose_file} up -d --wait",
                      log_error_stream_to_output=True
                      )


def start_container(container_name, image_name, image_tag='latest', docker_path='docker'):
    run_quiet_command("Start container",
                      f"{docker_path} run -it -v /var/run/docker.sock:/var/run/docker.sock --rm -d --name {container_name} {image_name}:{image_tag}")
    if not verify_container_is_running(container_name, docker_path):
        raise RuntimeError(f"Container ({container_name}) could not be restarted")


def verify_container_is_running(container_name, docker_path='docker'):
    container_run_cmd_output = run_quiet_command("check if container is running",
                                                 f"{docker_path} ps", return_process_output=True)
    if container_run_cmd_output is not None and container_name in container_run_cmd_output:
        return True
    else:
        return False


def verify_container_is_stopped(container_name, docker_path='docker'):
    container_stop_cmd_output = run_quiet_command("check if container is stopped",
                                                  f"{docker_path} ps -a", return_process_output=True
                                                  )
    if container_stop_cmd_output is not None and container_name in container_stop_cmd_output:
        return True
    else:
        return False


def stop_and_remove_container(container_name, docker_path='docker'):
    run_quiet_command(
        "stop and remove container",
        f"{docker_path} rm -f {container_name} || true"
    )


def remove_image(image_name, image_tag='latest', docker_path='docker'):
    run_quiet_command(
        "remove image",
        f"{docker_path} rmi {image_name}:{image_tag} || true"
    )


def verify_image_present(image_name, image_tag='latest', docker_path='docker'):
    container_images_cmd_ouptut = run_quiet_command("Check if image is present",
                                                    f"{docker_path} images", return_process_output=True)
    if container_images_cmd_ouptut is not None and re.search(image_name + r'\s+' + image_tag,
                                                             container_images_cmd_ouptut):
        return True
    else:
        return False


def copy_files_to_container(container_name, dir_path, file_path, docker_path='docker'):
    run_quiet_command(f"Create directory structure for copying files into container",
                      f"{docker_path} exec {container_name} mkdir -p {dir_path}")
    run_quiet_command(f"Copy file to container",
                      f"{docker_path} cp {file_path} {container_name}:{dir_path}/{os.path.basename(file_path)}")


def copy_files_from_container(container_name, dir_path, local_dir_path, docker_path='docker'):
    run_quiet_command(f"copy dir from container to local",
                      f"{docker_path} cp {container_name}:{dir_path}/. {local_dir_path}")


def read_file_from_container(container_name, file_path, docker_path='docker'):
    return run_quiet_command("read content of the file from container",
                             f" {docker_path} exec {container_name} cat {file_path}",
                             return_process_output=True)
