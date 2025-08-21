#!/bin/bash

set -e

# Check if the repository has been set from the environment variable
if [[ -z "$GITHUB_REPOSITORY" ]] ; then GITHUB_REPOSITORY=EBIvariation/eva-submission ; fi
if [[ -z "$GITHUB_REF" ]] ; then GITHUB_REF=master ; fi
if [[ -n "$GITHUB_SHA" ]] ; then GITHUB_REF=$GITHUB_SHA ; fi

git clone https://github.com/${GITHUB_REPOSITORY}.git eva-submission
cd eva-submission
git checkout ${GITHUB_REF}

python -m pip install .

cd ..

