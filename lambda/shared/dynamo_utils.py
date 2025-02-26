import os
import boto3
from typing import Dict, Any, List

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ITEMS_TABLE'])

def get_all_items() -> List[Dict[str, Any]]:
    response = table.scan()
    return response.get('Items', [])

def get_item(item_id: str) -> Dict[str, Any]:
    response = table.get_item(Key={'id': item_id})
    return response.get('Item')

def create_item(item: Dict[str, Any]) -> None:
    table.put_item(Item=item)

def update_item(item_id: str, updates: Dict[str, Any]) -> None:
    update_expression = "SET "
    expression_values = {}
    
    for key, value in updates.items():
        update_expression += f"#{key} = :{key}, "
        expression_values[f":{key}"] = value
    
    update_expression = update_expression.rstrip(", ")
    
    expression_names = {f"#{k}": k for k in updates.keys()}
    
    table.update_item(
        Key={'id': item_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values
    )

def delete_item(item_id: str) -> None:
    table.delete_item(Key={'id': item_id})
