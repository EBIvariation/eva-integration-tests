#!/bin/bash

set -e

# Check if the repository has been set from the environment variable
if [[ -z "$SOURCE_GITHUB_REPOSITORY" ]] ; then SOURCE_GITHUB_REPOSITORY=EBIvariation/eva-assembly-ingestion ; fi
if [[ -z "$SOURCE_GITHUB_REF" ]] ; then SOURCE_GITHUB_REF=main ; fi
if [[ -n "$SOURCE_GITHUB_SHA" ]] ; then SOURCE_GITHUB_REF=$SOURCE_GITHUB_SHA ; fi

echo "Clone https://github.com/${SOURCE_GITHUB_REPOSITORY}.git"

git clone https://github.com/${SOURCE_GITHUB_REPOSITORY}.git eva-assembly-ingestion
cd eva-assembly-ingestion
git checkout ${SOURCE_GITHUB_REF}

python -m pip -q install .

cd ..

