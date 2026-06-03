# EVA Integration Tests 
This repository contains integration tests for EVA (European Variation Archive) pipeline components. 
Each test suite starts the component under test plus all required supporting services in Docker containers, exercises it end-to-end, and asserts on the resulting database state or output files.

---

## Components

Each directory under `components/` represents one Docker image. Components fall into three categories:

### Real components: cloned from upstream source at build time

| Component | Source repository | Description |
|-----------|------------------|-------------|
| `eva_submission` | EBIvariation/eva-submission | Python + Nextflow end-to-end submission pipeline (validation, brokering, accession, ingestion) |
| `eva_sub_cli` | EBIvariation/eva-sub-cli | Python CLI used by external submitters |
| `eva_submission_ws` | EBIvariation/eva-submission-ws | Spring Boot REST API that coordinates submissions |
| `eva_ws` | EBIvariation/eva-ws | Spring Boot count-statistics REST API |
| `contig_alias_ws` | EBIvariation/contig-alias | Spring Boot contig-alias REST API |
| `eva_assembly_ingestion` | EBIvariation/eva-assembly-ingestion | Python + Nextflow assembly ingestion pipeline |
| `eva_release_automation` | EBIvariation/eva-release-automation | Python release automation pipeline and FTP publishing |

Real components that have an `install_repo.sh` script support being built from any fork or branch via the `SOURCE_GITHUB_REPOSITORY`, `SOURCE_GITHUB_REF`, and `SOURCE_GITHUB_SHA` Docker build arguments (see [Running tests on a different branch](#running-tests-on-a-different-branch)).

### Mock components: bespoke implementations that replace external services

| Component | Description |
|-----------|-------------|
| `mock_globus` | Flask app that replaces the Globus OAuth and transfer API used by the submission web service |
| `mock_ws` | Tomcat app that replaces external REST calls to ENA, BioSamples, and similar services |

### Infrastructure components

| Component | Base image | Description |
|-----------|-----------|-------------|
| `postgres_db` | postgres:11 | Multi-schema metadata database. Initialises with 9 SQL scripts covering `evapro`, `eva_submissions`, `eva_progress_tracker`, `eva_stats`, `eva_tasks`, and the variant/accession join-tables |
| `mongo_db` | mongo:6.0.24 | Sharded MongoDB cluster for variant entities (`submittedVariantEntity`, `clusteredVariantEntity`, etc.) |
| `oracle_db` | gvenzl/oracle-free:slim | ERA legacy schema used by the submission brokering pipeline |
| `mailhog` | mailhog | SMTP server + web UI that captures outbound emails sent during submission |

---

## Test suites

Each suite has its own docker-compose file and its own directory of pytest files:

| Suite | Compose file | Main container | Test directory |
|-------|-------------|----------------|----------------|
| EVA Submission | `docker-compose-eva-submission.yml` | `eva_submission_test` | `tests/components/eva_submission/` |
| EVA Sub CLI | `docker-compose-eva-sub-cli.yml` | `eva_sub_cli_test` | `tests/components/eva_sub_cli/` |
| Assembly Ingestion | `docker-compose-eva-assembly-ingestion.yml` | `eva_assembly_ingestion_test` | `tests/components/eva_assembly_ingestion/` |
| Release Automation | `docker-compose-eva-release-automation.yml` | `eva_release_automation_test` | `tests/components/eva_release_automation/` |

---

## Port and hostname wiring

Services in the same compose network communicate using their **container hostname** (the docker-compose service name) and the container's internal port. The `maven-settings.xml` file in `components/` defines a `docker` profile that uses these internal hostnames, and a `localhost` profile that uses `localhost` with the host-mapped ports for connecting from your developer machine.

| Service | Container hostname | Internal port | Host port (submission/sub-cli/assembly) | Host port (release automation) |
|---------|--------------------|:-------------:|:---------------------------------------:|:------------------------------:|
| PostgreSQL | `postgres_db` | 5432 | 5432 | 5433 |
| MongoDB | `mongo_db` | 27017 | 27017 | 27018 |
| Oracle | `oracle_db` | 1521 | 1521 | — |
| eva-submission-ws | `eva-submission-ws` | 8080 | 8080 | — |
| eva-ws | `eva-ws` | 8080 | 8083 | — |
| contig-alias | `contig-alias` | 8080 | 8081 | — |
| mock-ws | `mock-ws` | 8080 | 8082 | — |
| mock-globus | `mock-globus` | 5000 | 5000 | — |
| Mailhog SMTP | `mailhog` | 1025 | 1025 | — |
| Mailhog web UI | `mailhog` | 8025 | 8025 | — |

The release automation suite maps PostgreSQL to host port 5433 and MongoDB to 27018 so it can run concurrently alongside the other suites without port conflicts.

**Example**: when `eva_submission_ws` needs to write a record to PostgreSQL it connects to `postgres_db:5432` (resolved via Docker DNS). The same database is reachable from the host machine at `localhost:5432` for manual inspection, and `maven-settings.xml` exposes a `localhost` profile for this purpose.

---

## Running tests locally

Make sure Docker or Rancher is installed and running, then install the Python dependencies:

```bash
pip install -r requirements.txt
```

### Test against the upstream master branch

Run a full test suite:
```bash
PYTHONPATH=. pytest tests/components/eva_submission/
```

Run a single test file:
```bash
PYTHONPATH=. pytest tests/components/eva_submission/test_eva_submission_validation.py
```

The brokering tests require ENA credentials (a real Webin account used against the ENA test server):
```bash
EVA_SUBMISSION_WEBIN_USERNAME=Webin-XXXXX \
EVA_SUBMISSION_WEBIN_PASSWORD=******* \
PYTHONPATH=. pytest tests/components/eva_submission/test_eva_submission_brokering.py
```

The sub-CLI upload and submission tests also require ENA credentials:
```bash
WEBIN_TEST_USER_EMAIL=your@email \
WEBIN_TEST_USER_PASSWORD=******* \
PYTHONPATH=. pytest tests/components/eva_sub_cli/
```

**NOTE: The `eva_sub_cli` image is built for `linux/amd64`. On Apple Silicon Macs (M1/M2/M3) enable "Use Rosetta for x86/64 emulation on Apple Silicon" in Docker Desktop settings to avoid platform mismatch warnings or build failures.**

### Running tests on a different branch

A different fork and branch can be specified using environment variables:

```bash
SOURCE_GITHUB_REPOSITORY=tcezard/eva-submission \
SOURCE_GITHUB_REF=development_branch \
PYTHONPATH=. pytest tests/components/eva_submission/test_eva_submission_validation.py
```

**NOTE 1: The docker images are built again when the environment variables are changed. They have to be removed manually first:**

```bash
docker image rm eva_submission_test
```

**NOTE 2: Running on a different branch can only be done on one component at a time since the other components will rely on different repositories.**

### Forcing a full rebuild

If the Docker build cache is stale (e.g. after a rebase that changes SQL init scripts or config files), force a clean rebuild before running tests:

```bash
docker compose -f components/docker-compose-eva-submission.yml build --no-cache
# then recreate the containers
docker compose -f components/docker-compose-eva-submission.yml down
```

---

## Running tests on GitHub Actions

Two trigger mechanisms are in place:

### On push or pull request to `master`

`run-all-tests.yml` runs all four test suites in parallel using a job matrix. Each suite runs independently with `continue-on-error: true`, so a failure in one suite does not block the others.

### Repository dispatch (triggered by upstream component repos)

Each upstream repository can trigger its own suite by posting a `repository_dispatch` event to this repository, passing `SOURCE_GITHUB_REPOSITORY`, `SOURCE_GITHUB_REF`, and `SOURCE_GITHUB_SHA` in the payload. This lets a PR in (for example) `eva-submission` automatically run its integration tests here against the PR branch.

| Event type | Workflow file | Tests run |
|-----------|--------------|-----------|
| `trigger-eva-submission-tests` | `run-eva-submission-tests.yml` | `tests/components/eva_submission/` |
| `trigger-eva-sub-cli-tests` | `run-eva-sub-cli-tests.yml` | `tests/components/eva_sub_cli/` |
| `trigger-eva-assembly-ingestion-tests` | `run-eva-assembly-ingestion-tests.yml` | `tests/components/eva_assembly_ingestion/` |
| `trigger-eva-release-automation-tests` | `run-eva-release-automation-tests.yml` | `tests/components/eva_release_automation/` |

### Required GitHub secrets

| Secret | Used by                                       |
|--------|-----------------------------------------------|
| `EVA_SUBMISSION_WEBIN_USERNAME` | Submission brokering tests (real ENA account) |
| `EVA_SUBMISSION_WEBIN_PASSWORD` | Submission brokering tests                    |
| `WEBIN_TEST_USER_EMAIL` | Sub-CLI upload tests (ENA credentials)        |
| `WEBIN_TEST_USER_PASSWORD` | Sub-CLI upload tests                          |

