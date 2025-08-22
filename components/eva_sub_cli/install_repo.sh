#!/bin/bash

set -e

# Check if the repository has been set from the environment variable
if [[ -z "$GITHUB_REPOSITORY" ]] ; then GITHUB_REPOSITORY=EBIvariation/eva-sub-cli ; fi
if [[ -z "$GITHUB_REF" ]] ; then GITHUB_REF=main ; fi
if [[ -n "$GITHUB_SHA" ]] ; then GITHUB_REF=$GITHUB_SHA ; fi

echo "Clone https://github.com/${GITHUB_REPOSITORY}.git"

git clone https://github.com/${GITHUB_REPOSITORY}.git eva-sub-cli
cd eva-sub-cli
git checkout ${GITHUB_REF}

python -m pip install .

cd ..
