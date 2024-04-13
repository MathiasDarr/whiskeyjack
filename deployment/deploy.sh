#!/bin/bash

#aws cloudformation describe-stacks --stack-name BardNetworkingStack | jq .Stacks[0].Outputs > output.json
#vpc_id=$(cat output.json | jq '.[] | select(.OutputKey=="vpcidoutput").OutputValue')
#if [ -z ${vpc_id} ]; then echo "CANNOT FIND A VPC is unset"; else echo "var is set to '$vpc_id'"; fi

export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
cdk synth --parameters --require-approval never
cdk deploy --parameters --require-approval never