#!/usr/bin/env python3
import os

import aws_cdk as cdk

from deployment.ephemeral_stack import EphemeralStack

account = os.getenv("AWS_ACCOUNT")
region = "us-west-2"
env = cdk.Environment()
if account and region:
    env = cdk.Environment(account=account, region=region)

app = cdk.App()
EphemeralStack(app,
                "EphemeralStack",
                env=env
    )

app.synth()
