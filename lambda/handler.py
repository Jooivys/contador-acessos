import json
import boto3
import os

# Cria o cliente do DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])  # Nome da tabela vem da variável de ambiente

def handler(event, context):
    """
    Essa função é invocada pelo API Gateway.
    Ela incrementa o contador no DynamoDB e retorna o novo total.
    """

    # UpdateItem: incrementa o campo 'total' em +1 de forma atômica.
    # Se o item não existir, cria com total = 1 (ADD faz isso automaticamente).
    response = table.update_item(
        Key={"id": "hits"},                          # Partition Key fixa
        UpdateExpression="ADD #total :increment",    # Soma +1 no campo 'total'
        ExpressionAttributeNames={"#total": "total"},# 'total' é palavra reservada no DynamoDB
        ExpressionAttributeValues={":increment": 1},
        ReturnValues="UPDATED_NEW"                   # Retorna o novo valor após o update
    )

    novo_total = int(response["Attributes"]["total"])

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"       # Permite chamadas do browser (CORS)
        },
        "body": json.dumps({
            "count": novo_total,
            "message": f"{novo_total} pessoas já se interessaram!"
        })
    }
