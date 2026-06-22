from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    CfnOutput,
)
from constructs import Construct


class ContadorAcessosStack(Stack):
    """
    Stack CDK que cria toda a infraestrutura do contador de acessos.

    Recursos criados:
      1. Tabela DynamoDB  → guarda o contador
      2. Função Lambda    → incrementa o contador
      3. API Gateway      → expõe a URL pública

    Permissões (IAM):
      - Lambda recebe permissão de leitura/escrita na tabela via grant_read_write_data()
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── 1. DYNAMODB ───────────────────────────────────────────────────────
        tabela = dynamodb.Table(
            self, "TabelaContador",
            table_name="contador-acessos",

            # Partition Key: chave que identifica o item. Usamos "id" fixo = "hits".
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),

            # PAY_PER_REQUEST: paga só pelo uso, sem capacidade provisionada.
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,

            # DESTROY: apaga a tabela quando o stack for destruído.
            # Em produção, use RETAIN para não perder os dados.
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ── 2. LAMBDA ─────────────────────────────────────────────────────────
        funcao = _lambda.Function(
            self, "FuncaoContador",
            function_name="contador-acessos-handler",

            # Aponta para a pasta /lambda onde está o handler.py
            code=_lambda.Code.from_asset("lambda"),
            handler="handler.handler",           # arquivo.função
            runtime=_lambda.Runtime.PYTHON_3_12,

            # Passa o nome da tabela como variável de ambiente.
            environment={
                "TABLE_NAME": tabela.table_name
            },
        )

        # IAM: concede ao Lambda permissão de ler e escrever na tabela.
        tabela.grant_read_write_data(funcao)

        # ── 3. API GATEWAY ────────────────────────────────────────────────────
        api = apigw.RestApi(
            self, "ApiContador",
            rest_api_name="contador-acessos-api",
            description="API pública do contador de acessos serverless",

            # Habilita CORS para que o browser possa chamar a API diretamente
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["POST"],
            ),
        )

        # Cria o recurso /hits e associa o método POST à função Lambda
        hits = api.root.add_resource("hits")
        hits.add_method(
            "POST",
            apigw.LambdaIntegration(funcao)  # API GW invoca o Lambda
        )

        # ── 4. OUTPUTS ────────────────────────────────────────────────────────
        # Exibe a URL da API no terminal após o deploy
        CfnOutput(
            self, "UrlDaApi",
            value=f"{api.url}hits",
            description="URL pública do contador — faça um POST nessa URL"
        )

        CfnOutput(
            self, "NomeDaTabela",
            value=tabela.table_name,
            description="Nome da tabela DynamoDB"
        )
