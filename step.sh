#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Updating phase release for: ${package_name}"
if [ -z "$service_account_json_key_content" ] ; then
    echo "Downloading credentials from remote file"
    wget -O "${SCRIPT_DIR}/credentials.json" ${service_account_json_key_path}
else
    echo "Using local content credentials"
    echo "$service_account_json_key_content" > "${SCRIPT_DIR}/credentials.json"
fi
echo "Installing python dependencies"
pipenv install pyparsing==3.1.4
pipenv install google-api-python-client==2.86.0
pipenv install oauth2client
pipenv install urllib3

echo "Running: ${SCRIPT_DIR}/rollout_update.py ${package_name} ${SCRIPT_DIR}/credentials.json ${track} ${force_rollout}"
pipenv run python "${SCRIPT_DIR}/rollout_update.py" "${package_name}" "${SCRIPT_DIR}/credentials.json" "${track}" "${force_rollout}"

rm "${SCRIPT_DIR}/credentials.json"
