# Contador de Acessos — AWS Serverless

Arquitetura serverless para contar acessos em tempo real.

```
Usuário → API Gateway → Lambda → DynamoDB
```

## Pré-requisitos

- Python 3.12+
- Node.js 18+ (necessário para o CDK CLI)
- AWS CLI configurado (`aws configure`)
- CDK instalado: `npm install -g aws-cdk`

## Estrutura do projeto

```
contador-acessos/
├── app.py                          # Entry point do CDK
├── cdk.json                        # Configuração do CDK
├── requirements.txt                # Dependências Python
├── lambda/
│   └── handler.py                  # Código da função Lambda
└── lib/
    └── contador_acessos_stack.py   # Definição da infraestrutura (Stack CDK)
```

## app.py — Entry point do CDK

```python
#!/usr/bin/env python3
import aws_cdk as cdk
from lib.contador_acessos_stack import ContadorAcessosStack

app = cdk.App()

ContadorAcessosStack(
    app, "ContadorAcessosStack",
    # Descomente e ajuste para fazer deploy em uma conta/região específica:
    # env=cdk.Environment(account="123456789012", region="us-east-1"),
)

app.synth()
```

## Deploy

```bash
# 1. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate.bat       # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Bootstrap (só na primeira vez por conta/região)
cdk bootstrap

# 4. Visualize o que será criado
cdk diff

# 5. Faça o deploy
cdk deploy
```

Após o deploy, o CDK exibe a URL da API. Exemplo:
```
Outputs:
ContadorAcessosStack.UrlDaApi = https://abc123.execute-api.us-east-1.amazonaws.com/prod/hits
```

## Testando

```bash
# Incrementa o contador e retorna o total (método POST)
curl -X POST https://SEU-ENDPOINT/prod/hits

# Resposta esperada:
# {"count": 1, "message": "1 pessoas já se interessaram!"}
```

## Como funciona

| Serviço | Papel | Por que foi escolhido |
|---|---|---|
| API Gateway | Expõe URL pública | Gerencia HTTPS, CORS e throttling automaticamente |
| Lambda | Executa a lógica | Serverless — acorda só quando chamado, escala ilimitado |
| DynamoDB | Persiste o contador | `UpdateItem` atômico — sem conflito com 1M acessos simultâneos |

## Permissões IAM criadas automaticamente

O CDK chama `tabela.grant_read_write_data(funcao)` que cria uma IAM Policy com:
- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:UpdateItem`
- `dynamodb:DeleteItem`
- `dynamodb:Query`
- `dynamodb:Scan`

## Destruir a infraestrutura

```bash
cdk destroy
```

> ⚠️ A tabela DynamoDB está com `RemovalPolicy.DESTROY`. Em produção, mude para `RETAIN`.