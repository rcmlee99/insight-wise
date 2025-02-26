from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_cloudwatch as cloudwatch,
    aws_kinesis as kinesis,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class ItemAPIStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool
        user_pool = cognito.UserPool(
            self, "ItemsUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            removal_policy=RemovalPolicy.DESTROY  # For development, use RETAIN for production
        )

        # Create app client
        client = user_pool.add_client("ItemsWebClient",
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True
                ),
                scopes=[cognito.OAuthScope.OPENID],
                callback_urls=["http://localhost:5000/callback"]
            )
        )

        # Create Grafana workspace
        grafana_workspace = grafana.CfnWorkspace(
            self, "ItemsAPIGrafana",
            account_access_type="CURRENT_ACCOUNT",
            authentication_providers=["SAML"],
            permission_type="SERVICE_MANAGED",
            role_arn=self.create_grafana_role().role_arn,
            data_sources=["CLOUDWATCH", "PROMETHEUS"],
            name="items-api-monitoring"
        )

        # Create Kinesis Data Stream
        log_stream = kinesis.Stream(
            self, "ItemsAPILogStream",
            stream_name="items-api-logs",
            retention_period=Duration.hours(24),
            shard_count=1,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create CloudWatch Log Group with Kinesis subscription
        log_group = cloudwatch.LogGroup(
            self, "ItemsAPILogs",
            log_group_name="/aws/lambda/items-api",
            retention=cloudwatch.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "ItemsAPIDashboard",
            dashboard_name="items-api-metrics"
        )

        # Add dashboard widgets
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Latency",
                left=[
                    cloudwatch.Metric(
                        namespace="ItemsAPI",
                        metric_name="APILatency",
                        statistic="avg",
                        period=Duration.minutes(1)
                    )
                ]
            ),
            cloudwatch.GraphWidget(
                title="API Status Codes",
                left=[
                    cloudwatch.Metric(
                        namespace="ItemsAPI",
                        metric_name="APIStatus",
                        statistic="sum",
                        period=Duration.minutes(1)
                    )
                ]
            )
        )

        # Create MongoDB table
        items_table = dynamodb.Table(
            self, "ItemsTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # For development, use RETAIN for production
        )

        # Create Lambda layers
        shared_layer = _lambda.LayerVersion(
            self, "SharedLayer",
            code=_lambda.Code.from_asset("lambda/shared"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Layer containing shared utilities and external dependencies"
        )

        # Common Lambda configuration
        lambda_environment = {
            "USER_POOL_ID": user_pool.user_pool_id,
            "CLIENT_ID": client.user_pool_client_id,
            "LOG_LEVEL": "INFO",
            "POWERTOOLS_SERVICE_NAME": "items-api",
            "POWERTOOLS_METRICS_NAMESPACE": "ItemsAPI",
            "KINESIS_STREAM_NAME": log_stream.stream_name
        }

        # Create mock Kinesis consumer Lambda
        mock_consumer = _lambda.Function(
            self, "MockKinesisConsumer",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="mock_consumer.handler",
            environment=lambda_environment
        )

        # Grant permissions to write to Kinesis stream
        log_stream.grant_write(mock_consumer)

        # Create other Lambda functions with Kinesis permissions
        create_function = _lambda.Function(
            self, "CreateItemFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="create_item.handler",
            environment=lambda_environment,
            layers=[shared_layer]
        )
        log_stream.grant_write(create_function)

        get_items_function = _lambda.Function(
            self, "GetItemsFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="get_items.handler",
            environment=lambda_environment,
            layers=[shared_layer]
        )
        log_stream.grant_write(get_items_function)

        get_item_function = _lambda.Function(
            self, "GetItemFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="get_item.handler",
            environment=lambda_environment,
            layers=[shared_layer]
        )
        log_stream.grant_write(get_item_function)

        update_function = _lambda.Function(
            self, "UpdateItemFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="update_item.handler",
            environment=lambda_environment,
            layers=[shared_layer]
        )
        log_stream.grant_write(update_function)

        delete_function = _lambda.Function(
            self, "DeleteItemFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="delete_item.handler",
            environment=lambda_environment,
            layers=[shared_layer]
        )
        log_stream.grant_write(delete_function)


        # Create Authorizer
        auth = apigateway.CognitoUserPoolsAuthorizer(
            self, "ItemsAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # Create API Gateway
        api = apigateway.RestApi(
            self, "ItemsApi",
            rest_api_name="Items API",
            description="API for managing items"
        )

        # Add authorization to all methods
        auth_settings = apigateway.MethodOptions(
            authorizer=auth,
            authorization_type=apigateway.AuthorizationType.COGNITO
        )

        items = api.root.add_resource("items")
        items.add_method("GET", apigateway.LambdaIntegration(get_items_function), auth_settings)
        items.add_method("POST", apigateway.LambdaIntegration(create_function), auth_settings)

        item = items.add_resource("{id}")
        item.add_method("GET", apigateway.LambdaIntegration(get_item_function), auth_settings)
        item.add_method("PATCH", apigateway.LambdaIntegration(update_function), auth_settings)
        item.add_method("DELETE", apigateway.LambdaIntegration(delete_function), auth_settings)

    def create_grafana_role(self):
        """Create IAM role for Grafana workspace"""
        role = iam.Role(
            self, "GrafanaWorkspaceRole",
            assumed_by=iam.ServicePrincipal("grafana.amazonaws.com"),
            description="Role for Grafana workspace to access CloudWatch"
        )

        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSGrafanaCloudWatchAccess")
        )

        return role