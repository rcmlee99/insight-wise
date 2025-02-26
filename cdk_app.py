#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_stack import ItemAPIStack

app = cdk.App()

# Use environment variables or default values for account/region
env = cdk.Environment(
    account=os.environ.get('CDK_DEFAULT_ACCOUNT', '123456789012'),  # Default account
    region=os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')        # Default region
)

stack = ItemAPIStack(app, "ItemAPIStack", env=env)
app.synth()
