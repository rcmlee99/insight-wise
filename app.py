#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_stack import ItemAPIStack
from flask import Flask
from shared.mongo_utils import get_mongo_collection

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Initialize MongoDB connection
get_mongo_collection()

# Import routes after app is created to avoid circular imports
from routes import *

#This section remains from the original code.
cdk_app = cdk.App()

# Use environment variables or default values for account/region
env = cdk.Environment(
    account=os.environ.get('CDK_DEFAULT_ACCOUNT', '123456789012'),  # Default account
    region=os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')        # Default region
)

stack = ItemAPIStack(cdk_app, "ItemAPIStack", env=env)
cdk_app.synth()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)