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
