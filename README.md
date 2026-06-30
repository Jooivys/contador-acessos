# Contador de Acessos — AWS Serverless

API serverless que conta acessos em tempo real. Cada requisição `POST` incrementa um contador persistido no DynamoDB e devolve o total atualizado.

<img width="933" height="282" alt="arquitetura-serverless" src="https://github.com/user-attachments/assets/4a85702f-b05a-4c22-9ef2-482bade50efb"/>


## Análise do projeto

| Aspecto | Detalhe |
|---|---|
| **Propósito** | Expor uma URL pública que incrementa e retorna um contador de acessos |
| **IaC** | AWS CDK v2 (Python) — infraestrutura definida como código |
| **Runtime** | Python 3.12 na Lambda; `boto3` já vem no runtime da AWS |
| **Persistência** | DynamoDB com billing `PAY_PER_REQUEST` (sem capacidade provisionada) |
| **Endpoint** | `POST /hits` com CORS habilitado para chamadas do browser |
| **Atomicidade** | `UpdateItem` com `ADD` garante incremento seguro mesmo com acessos simultâneos |

### Recursos criados no deploy

| Recurso AWS | Nome | Função |
|---|---|---|
| DynamoDB Table | `contador-acessos` | Armazena o contador (`id = "hits"`, campo `total`) |
| Lambda Function | `contador-acessos-handler` | Executa a lógica de incremento |
| API Gateway REST | `contador-acessos-api` | Expõe a rota pública `/hits` |
| IAM Policy | (gerada automaticamente) | Lambda com leitura/escrita na tabela |

### Estrutura do repositório

```
contador-acessos/
├── app.py                          # Entry point do CDK
├── cdk.json                        # Configuração do CDK CLI
├── requirements.txt                # Dependências Python (CDK)
├── lambda/
│   └── handler.py                  # Código da função Lambda
└── lib/
    └── contador_acessos_stack.py   # Stack CDK (DynamoDB + Lambda + API GW)
```

---

## Pré-requisitos

Instale e configure **todos** os itens abaixo antes do deploy.

### 1. Conta AWS

- Conta AWS ativa com permissões para criar: CloudFormation, Lambda, DynamoDB, API Gateway, IAM e S3 (bucket do bootstrap).
- Usuário ou role com permissões equivalentes a `PowerUserAccess` + IAM (ou uma policy customizada para CDK).

### 2. Python 3.12+

Verifique a versão:

```powershell
python --version
```

O runtime da Lambda está definido como **Python 3.12** em `lib/contador_acessos_stack.py`.

### 3. Node.js 18+

Necessário para instalar e executar o **AWS CDK CLI**:

```powershell
node --version
npm --version
```

### 4. AWS CLI v2

Instale e configure credenciais da sua conta:

```powershell
aws --version
aws configure
```

O comando `aws configure` solicita:

| Campo | Descrição |
|---|---|
| `AWS Access Key ID` | Chave de acesso do IAM |
| `AWS Secret Access Key` | Segredo da chave |
| `Default region name` | Região do deploy (ex.: `us-east-1`, `sa-east-1`) |
| `Default output format` | Pode deixar `json` |

**Alternativa:** variáveis de ambiente em vez de `aws configure`:

```powershell
$env:AWS_ACCESS_KEY_ID="sua-chave"
$env:AWS_SECRET_ACCESS_KEY="seu-segredo"
$env:AWS_DEFAULT_REGION="sa-east-1"
```

Teste se a autenticação funciona:

```powershell
aws sts get-caller-identity
```

### 5. AWS CDK CLI

Instale globalmente via npm:

```powershell
npm install -g aws-cdk
cdk --version
```

Recomendado: CDK **2.100.0** ou superior (compatível com `aws-cdk-lib` do `requirements.txt`).

---

## Configuração do projeto

### 1. Clone o repositório e entre na pasta

```powershell
cd contador-acessos
```

### 2. Ambiente virtual Python

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> No Linux/macOS: `source .venv/bin/activate`

### 3. Instale as dependências do CDK

```powershell
pip install -r requirements.txt
```

### 4. (Opcional) Fixar conta e região no CDK

Por padrão, o CDK usa a conta e região configuradas no AWS CLI. Para fixar explicitamente, edite `app.py`:

```python
ContadorAcessosStack(
    app, "ContadorAcessosStack",
    env=cdk.Environment(account="123456789012", region="sa-east-1"),
)
```

### 5. Bootstrap (obrigatório na 1ª vez por conta/região)

O CDK precisa de um bucket S3 e roles IAM para publicar assets. Execute **uma vez** por combinação conta + região:

```powershell
cdk bootstrap
```

Com perfil nomeado:

```powershell
cdk bootstrap --profile meu-projeto
```

---

## Deploy

```powershell
# Visualizar mudanças antes de aplicar
cdk diff

# Criar/atualizar a infraestrutura
cdk deploy
```

Confirme com `y` quando solicitado. Ao final, o CDK exibe os outputs:

```
Outputs:
ContadorAcessosStack.UrlDaApi = https://abc123.execute-api.sa-east-1.amazonaws.com/prod/hits
ContadorAcessosStack.NomeDaTabela = contador-acessos
```

Guarde a **UrlDaApi** — é o endpoint público do contador.

---

## Testando

### Via curl (PowerShell)

```powershell
curl.exe -X POST "https://SEU-ENDPOINT/prod/hits"
```

### Via Invoke-WebRequest (PowerShell nativo)

```powershell
Invoke-RestMethod -Method POST -Uri "https://SEU-ENDPOINT/prod/hits"
```

### Resposta esperada

```json
{
  "count": 1,
  "message": "1 pessoas já se interessaram!"
}
```

Cada nova requisição `POST` incrementa `count` em 1. Requisições `GET` não são suportadas (apenas `POST /hits`).

### Teste no browser (JavaScript)

```javascript
fetch("https://SEU-ENDPOINT/prod/hits", { method: "POST" })
  .then(r => r.json())
  .then(console.log);
```

O CORS está habilitado para todas as origens (`*`).

---

## Como funciona internamente

1. **API Gateway** recebe `POST /hits` e invoca a Lambda.
2. **Lambda** (`lambda/handler.py`) lê `TABLE_NAME` da variável de ambiente e executa:
   - `UpdateItem` com chave `id = "hits"`
   - `ADD total :increment` (operação atômica no DynamoDB)
3. **DynamoDB** retorna o novo valor de `total`.
4. **Lambda** responde com JSON `{ "count": N, "message": "..." }`.

### Permissões IAM (criadas automaticamente)

O CDK chama `tabela.grant_read_write_data(funcao)`, concedendo à Lambda:

- `dynamodb:GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Query`, `Scan`

---

## Comandos úteis

| Comando | Descrição |
|---|---|
| `cdk synth` | Gera o template CloudFormation sem deploy |
| `cdk diff` | Compara stack local com o que está na AWS |
| `cdk deploy` | Cria ou atualiza a infraestrutura |
| `cdk destroy` | Remove todos os recursos do stack |

---

## Destruir a infraestrutura

```powershell
cdk destroy
```

> **Atenção:** a tabela DynamoDB está com `RemovalPolicy.DESTROY` — os dados do contador serão apagados junto com o stack. Em produção, altere para `RemovalPolicy.RETAIN` em `lib/contador_acessos_stack.py`.

---

## Solução de problemas

| Problema | Possível causa | Solução |
|---|---|---|
| `Unable to resolve AWS account` | Credenciais não configuradas | Execute `aws configure` ou defina `AWS_PROFILE` |
| `This stack uses assets, so the toolkit stack must be deployed` | Bootstrap não feito | Execute `cdk bootstrap` na região correta |
| `Access Denied` no deploy | IAM insuficiente | Verifique permissões do usuário/role |
| `python3: command not found` (Windows) | Alias incorreto | Use `python` em vez de `python3`, ou ajuste `cdk.json` |
| Script de activate bloqueado (Windows) | Política de execução | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## Custos estimados

Para tráfego baixo/moderado, o custo tende a ficar dentro do **free tier** da AWS:

- Lambda: 1M requisições/mês grátis
- DynamoDB on-demand: 25 GB de armazenamento grátis
- API Gateway: 1M chamadas/mês grátis (REST API, primeiros 12 meses)

Consulte a [calculadora de preços da AWS](https://calculator.aws/) para estimativas com o seu volume de acessos.

---

## Produção — recomendações

- Alterar `RemovalPolicy.DESTROY` para `RemovalPolicy.RETAIN` na tabela DynamoDB
- Restringir CORS (`allow_origins`) ao domínio do seu frontend
- Adicionar throttling/rate limiting no API Gateway
- Configurar alarmes CloudWatch para erros da Lambda
- Considerar autenticação (API Key, Cognito ou authorizer customizado) se o contador não deve ser público
