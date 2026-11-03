
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

## Atualização visual
A interface foi modernizada com cabeçalho, navegação por abas mais limpa, cartões de indicadores, formulários organizados, botões com hierarquia visual e diferenciação de status dos barris por cor. A lógica de vendas, limpeza de barril, alertas e relatórios permanece preservada.

## Atualização: relatório com filtros
A aba **Relatório** foi transformada em um painel de análise com:

- filtro por período: todo o histórico, hoje, últimos 7 dias, últimos 30 dias, mês atual ou intervalo personalizado;
- filtro por cerveja;
- filtro pela situação atual do barril: cheio, parcial ou vazio;
- indicadores de quantidade de vendas, litros vendidos, média em mL por venda e quantidade de barris envolvidos;
- tabela detalhada das vendas encontradas;
- ranking de consumo por cerveja;
- exportação do resultado filtrado para CSV.

## Venda personalizada e limpeza de barril
- Além dos copos de 300 mL, 400 mL, 500 mL e 1 L, é possível informar uma quantidade específica em mL.
- Barris com menos de 1,5 L podem ser limpos pelo botão **Limpar barril**.
- A limpeza zera o saldo do barril, mas **não é registrada como venda nem como consumo**.

## Atualização: login e relatórios avançados

A versão atual passou a contar com uma tela de autenticação antes do acesso ao sistema.

### Acesso inicial

- **Usuário:** `admin`
- **Senha:** `BeerFlow@2026`

As credenciais são armazenadas no SQLite com hash PBKDF2 e salt individual. O menu lateral também exibe a sessão ativa e possui opção de **Sair**, retornando para a tela de login.

### Nova área de relatórios

O relatório foi reorganizado em duas telas internas:

- **Visão geral:** indicadores de vendas, litros vendidos, média por venda e barris envolvidos; cerveja mais vendida; maior venda; estoque disponível; gráfico de evolução diária; e ranking por cerveja.
- **Vendas detalhadas:** tabela completa das movimentações que atendem aos filtros selecionados.

Os filtros disponíveis agora incluem:

- período;
- cerveja;
- barril específico;
- status atual do barril;
- intervalo personalizado de datas.

A exportação em CSV foi mantida e agora também informa o tipo da venda: copo de 300 mL, 400 mL, 500 mL, 1 L ou quantidade personalizada.

## Atualização visual

A identidade visual foi refinada para manter o BeerFlow com aparência de painel profissional: login em duas áreas, menu lateral com sessão do usuário, componentes mais consistentes, abas internas de relatório, indicadores compactos e novos elementos gráficos.

## Atualização: pesquisa de estoque e atualização confirmada de relatórios

A aba **Estoque** passou a contar com filtros de pesquisa por:

- ID do barril ou nome da cerveja;
- cerveja específica;
- status: Cheio, Em consumo, Nível crítico ou Vazio.

A busca por texto é atualizada enquanto o usuário digita e a tela informa quantos barris correspondem aos filtros atuais. O botão **Limpar filtros** restaura a visão completa do estoque.

Na aba **Relatório**, o botão **Atualizar relatórios** solicita confirmação antes de recarregar indicadores, ranking e tabela conforme os filtros atuais. O botão **Aplicar filtros** continua funcionando diretamente para facilitar a consulta.
