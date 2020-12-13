#!/bin/bash

set -eu

cat << EOE
ACTIVATION_CODE: $ACTIVATION_CODE
$ACTIVATION_ID: $ACTIVATION_ID
REGION: $REGION
EOE

if [[ -z $ACTIVATION_CODE || -z $ACTIVATION_ID || -z $REGION ]]; then
  echo '$ACTIVATION_CODE, $ACTIVATION_ID and $REGION are required.' 1>&2
  exit 1
fi

/usr/bin/amazon-ssm-agent -register -code $ACTIVATION_CODE -id $ACTIVATION_ID -region $REGION

/usr/bin/amazon-ssm-agent
