// lib/api-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as kinesis from 'aws-cdk-lib/aws-kinesis';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class ApiStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // Cognito User Pool
        const userPool = new cognito.UserPool(this, 'UserPool', {
            selfSignUpEnabled: true,
            signInAliases: { email: true },
        });

        const userPoolClient = new cognito.UserPoolClient(this, 'UserPoolClient', {
            userPool,
        });

        // SNS Topic
        const topic = new sns.Topic(this, 'ResultTopic');

        // Kinesis Stream
        const stream = new kinesis.Stream(this, 'LogStream');

        // Lambda Function
        const itemLocationLambda = new lambda.Function(this, 'ItemLocationLambda', {
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'handler.main',
            code: lambda.Code.fromAsset('lambda'),
            environment: {
                SNS_TOPIC_ARN: topic.topicArn,
                KINESIS_STREAM_NAME: stream.streamName,
            },
        });

        // Permissions
        topic.grantPublish(itemLocationLambda);
        stream.grantWrite(itemLocationLambda);

        // API Gateway with Cognito Auth
        const api = new apigateway.RestApi(this, 'ItemLocationAPI', {
            restApiName: 'ItemLocationService',
            defaultCorsPreflightOptions: {
                allowOrigins: apigateway.Cors.ALL_ORIGINS,
                allowMethods: apigateway.Cors.ALL_METHODS,
            },
        });

        const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'APIAuthorizer', {
            cognitoUserPools: [userPool],
        });

        const items = api.root.addResource('items');

        // Request Model Schema for Item Validation
        const itemModel = api.addModel('ItemModel', {
            contentType: 'application/json',
            modelName: 'ItemModel',
            schema: {
                type: apigateway.JsonSchemaType.OBJECT,
                required: ['name', 'postcode', 'startDate'],
                properties: {
                    name: { type: apigateway.JsonSchemaType.STRING, maxLength: 50 },
                    postcode: { type: apigateway.JsonSchemaType.STRING, pattern: '^\d{5}$' },
                    latitude: { type: apigateway.JsonSchemaType.NUMBER },
                    longitude: { type: apigateway.JsonSchemaType.NUMBER },
                    directionFromNewYork: {
                        type: apigateway.JsonSchemaType.STRING,
                        enum: ['NE', 'NW', 'SE', 'SW']
                    },
                    title: { type: apigateway.JsonSchemaType.STRING },
                    users: {
                        type: apigateway.JsonSchemaType.ARRAY,
                        items: { type: apigateway.JsonSchemaType.STRING, maxLength: 50 }
                    },
                    startDate: { type: apigateway.JsonSchemaType.STRING, format: 'date-time' }
                }
            }
        });

        // POST /items with Request Validator
        items.addMethod('POST', new apigateway.LambdaIntegration(itemLocationLambda), {
            authorizer,
            authorizationType: apigateway.AuthorizationType.COGNITO,
            requestModels: {
                'application/json': itemModel
            },
            requestValidator: new apigateway.RequestValidator(this, 'RequestValidator', {
                restApi: api,
                validateRequestBody: true,
                validateRequestParameters: true,
            }),
        });

        // Other methods remain the same
        items.addMethod('GET', new apigateway.LambdaIntegration(itemLocationLambda), {
            authorizer,
            authorizationType: apigateway.AuthorizationType.COGNITO,
        });

        const itemById = items.addResource('{id}');
        itemById.addMethod('GET', new apigateway.LambdaIntegration(itemLocationLambda), {
            authorizer,
            authorizationType: apigateway.AuthorizationType.COGNITO,
        });

        itemById.addMethod('PATCH', new apigateway.LambdaIntegration(itemLocationLambda), {
            authorizer,
            authorizationType: apigateway.AuthorizationType.COGNITO,
        });

        itemById.addMethod('DELETE', new apigateway.LambdaIntegration(itemLocationLambda), {
            authorizer,
            authorizationType: apigateway.AuthorizationType.COGNITO,
        });

        new logs.LogGroup(this, 'LambdaLogGroup', {
            logGroupName: `/aws/lambda/${itemLocationLambda.functionName}`,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
        });
    }
}
