
# BeerFlow

Protótipo acadêmico de um sistema de acompanhamento automatizado de barris para eventos cervejeiros.

## Funcionalidade principal implementada

O sistema permite cadastrar barris e registrar vendas. A cada venda:

1. o operador informa a quantidade vendida em mililitros;
2. o sistema converte a quantidade para litros;
3. desconta automaticamente o volume do barril;
4. atualiza o estoque disponível;
5. verifica se o barril atingiu o nível crítico;
6. gera um alerta automaticamente quando necessário.

Isso demonstra o fluxo:

**Input → Processamento → Output**

### Exemplo

- Volume inicial: 10 L
- Venda: 500 ml
- Processamento: 10 L - 0,5 L
- Saída: 9,5 L restantes

Quando o volume fica igual ou abaixo de 5 litros, o sistema gera um alerta.

## Tecnologias

- Python 3
- Tkinter
- SQLite

> Nesta versão inicial foi utilizado SQLite para facilitar a demonstração e execução do projeto sem necessidade de instalar um servidor de banco de dados. A estrutura pode posteriormente ser migrada para PostgreSQL.

## Como executar

1. Instale o Python 3.
2. Baixe ou clone este repositório.
3. Abra o terminal na pasta do projeto.
4. Execute:

```bash
python main.py
```

O banco `beerflow.db` será criado automaticamente na primeira execução.

## O que mostrar no vídeo

1. Abrir o BeerFlow.
2. Cadastrar um barril, por exemplo:
   - Cerveja: IPA
   - Volume: 10 litros
3. Registrar uma venda de 500 ml.
4. Mostrar que o volume cai automaticamente para 9,5 litros.
5. Fazer novas vendas até o barril ficar com 5 litros ou menos.
6. Mostrar o alerta automático.
7. Abrir a aba "Alertas".
8. Abrir a aba "Relatório".
9. Mostrar rapidamente o código no GitHub.

## Estrutura

- `main.py` — aplicação principal
- `beerflow.db` — banco gerado automaticamente após execução
- `README.md` — documentação do projeto
- `.gitignore` — arquivos que não precisam ser enviados ao GitHub

## Atualização: controle de estoque de barris

A versão atual também permite:

- visualizar a quantidade de barris **cheios**;
- visualizar a quantidade de barris **parcialmente vendidos**;
- visualizar a quantidade de barris **vazios**;
- adicionar vários novos barris de uma cerveja que já está cadastrada, sem precisar cadastrar novamente o nome da cerveja;
- informar o volume e a quantidade dos novos barris recebidos;
- consultar os mesmos números no relatório automático.

### Classificação dos barris

- **Cheio:** o volume atual é igual ao volume total do barril;
- **Parcialmente vendido:** já houve retirada de volume, mas ainda há cerveja disponível;
- **Vazio:** o volume chegou a zero.

## Atualização de entrada e vendas
- Campos de volume aceitam apenas números e um separador decimal (vírgula ou ponto).
- Quantidade de barris aceita apenas números inteiros.
- O registro de venda usa tamanhos fixos: 300 ml, 400 ml, 500 ml ou 1 L.
