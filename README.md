# Run the integration test locally

Make sure that Docker is installed and Running

## Test on upstream/master
In eva-integration_tests directory, running the following command will pull the master branch of eva-submission and test validation
```
PYTHONPATH=. pytest tests/components/eva_submission/test_eva_submission_validation.py
```

The brokering needs integration tests needs ENA credentials that can be provided through environment variables
```
EVA_SUBMISSION_WEBIN_USERNAME=webin-123456 \
EVA_SUBMISSION_WEBIN_PASSWORD=******* \
PYTHONPATH=. pytest tests/components/eva_submission/test_eva_submission_brokering.py
```

## Test a different branch

A different fork and branch can be specified using environment variables

```
SOURCE_GITHUB_REPOSITORY=tcezard/eva-submission \
SOURCE_GITHUB_REF=development_branch \
PYTHONPATH=. pytest tests/components/eva_submission/test_eva_submission_validation.py
```

**NOTE1: The docker images are built again when the environment variable are changed. They have to be removed manually first**

```
docker image rm eva_submission_test
```

**NOTE2: Running on a different branch can only be done on one component at a time since the other components will rely on different repositories**
