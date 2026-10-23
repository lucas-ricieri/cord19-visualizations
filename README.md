# Visualizações da literatura científica sobre COVID-19

Projeto desenvolvido no contexto de um Trabalho de Conclusão de Curso (TCC) para explorar publicações do CORD-19 entre 2020 e 2022. O processamento combina curadoria bibliográfica, modelagem de tópicos com LDA e visualização da produção de autores ao longo dos anos.

O fluxo está organizado em seis notebooks, com explicações e operações apresentadas passo a passo. Os módulos em `src/` concentram rotinas de apoio.

## Visualizações

[Acesse a página do projeto](https://lucas-ricieri.github.io/cord19-visualizations/Page/).

| Resultado | LDA — 20 tópicos | Streamgraph de autores |
|---|---|---|
| Amostra | [Explorar tópicos](https://lucas-ricieri.github.io/cord19-visualizations/outputs/amostras/lda.html) | [Explorar autores](https://lucas-ricieri.github.io/cord19-visualizations/outputs/amostras/streamgraph_autores.html) |
| Completo | [Explorar tópicos](https://lucas-ricieri.github.io/cord19-visualizations/outputs/completos/lda.html) | [Explorar autores](https://lucas-ricieri.github.io/cord19-visualizations/outputs/completos/streamgraph_autores.html) |

Na versão amostrada do LDA, são selecionados 200 mil documentos sem reposição. No streamgraph completo, são considerados os 15% de nomes com mais publicações; a versão amostrada sorteia 50 mil nomes dentro desse grupo e preserva suas contagens de produção. Os dois sorteios usam semente 42.

Para visualizar os resultados sem executar o processamento, use a página publicada ou abra `Page/index.html` localmente. Os links da tabela acima abrem diretamente as visualizações publicadas no GitHub Pages.

## Dados necessários

A base utilizada é o **CORD-19, release de 2 de junho de 2022**. Para executar o projeto, forneça estes dois arquivos:

Os conteúdos da pasta `data/`, **exceto o arquivo bruto do CORD-19 (`metadata.csv`)**, podem ser baixados neste [pacote de dados no Google Drive](https://drive.google.com/drive/folders/1oKGwwVravFk7TFOE_JDjkpXKYSpbUHkl?usp=sharing). Coloque os arquivos em `data/`, preservando a estrutura de subpastas do pacote. O CSV bruto deve ser baixado separadamente pelo link indicado abaixo.

| Arquivo | Como obter | Destino no projeto |
|---|---|---|
| `metadata.csv` | [Download do CSV](https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2022-06-02/metadata.csv) · [Repositório oficial do CORD-19](https://github.com/allenai/cord19) | `data/raw/cord19_2022-06-02/metadata.csv` |
| `checkpoint_enriquecimento.json` | Incluído no [pacote de dados no Google Drive](https://drive.google.com/drive/folders/1oKGwwVravFk7TFOE_JDjkpXKYSpbUHkl?usp=sharing) | `data/checkpoints/recuperacao_dados/checkpoint_enriquecimento.json` |

O download do CSV é manual. O fluxo principal lê o checkpoint para preencher campos ausentes e não faz novas consultas ao OpenAlex. Os dados brutos, os checkpoints e os modelos não acompanham o repositório; os quatro HTMLs finais estão incluídos.

As fontes e os destinos também estão registrados em [configuracao/fontes_dados.csv](configuracao/fontes_dados.csv).

## Instalação

O ambiente utilizado nas execuções do projeto foi **Python 3.12, 64 bits**. As dependências e o modelo linguístico do spaCy estão declarados em `requirements.txt`.

```bash
git clone https://github.com/lucas-ricieri/cord19-visualizations.git
cd cord19-visualizations
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
# Windows — PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux ou macOS
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Opcionalmente, copie `.env.example` para `.env` e configure `CORD19_METADATA` para indicar outro caminho para o CSV ou `CORD19_DATA_DIR` para alterar a pasta de dados.

## Execução

Coloque os dois arquivos de entrada nos destinos indicados e execute os comandos a partir da raiz do projeto.

### Pelos notebooks

```bash
python -m jupyterlab
```

Selecione o ambiente virtual como kernel e execute os notebooks nesta ordem:

| Notebook | Etapa |
|---|---|
| [01_exploracao_limpeza.ipynb](notebooks/01_exploracao_limpeza.ipynb) | Exploração do CSV, deduplicação e separação dos registros completos e incompletos |
| [02_enriquecimento_consolidacao.ipynb](notebooks/02_enriquecimento_consolidacao.ipynb) | Aplicação do checkpoint e consolidação dos registros |
| [03_exploracao_periodo.ipynb](notebooks/03_exploracao_periodo.ipynb) | Curadoria dos conflitos de DOI e recorte de 2020 a 2022 |
| [04_lda.ipynb](notebooks/04_lda.ipynb) | Processamento textual, corpus BOW, LDA completo e pyLDAvis |
| [05_streamgraph_autores.ipynb](notebooks/05_streamgraph_autores.ipynb) | Contagem de autorias, ranking, amostragem, CSVs e streamgraphs |
| [06_amostragem_lda.ipynb](notebooks/06_amostragem_lda.ipynb) | Amostragem dos documentos, LDA e pyLDAvis amostrado |

### Pelo terminal

Para executar os seis notebooks sequencialmente:

```bash
python -m src.executar_pipeline
```

Na primeira execução, as etapas constroem os resultados ausentes. Nas seguintes, os notebooks de modelagem e autores podem reutilizar os resultados locais existentes. Para refazer o processamento e os modelos:

```bash
python -m src.executar_pipeline --reprocessar
```

A lematização preserva blocos concluídos para permitir retomada após interrupções. Isso é independente do checkpoint bibliográfico de entrada. Ao alterar os dados ou os critérios científicos, reexecute as etapas dependentes.

Para executar somente um notebook, mantendo suas entradas anteriores disponíveis:

```bash
python -m src.executar_pipeline --notebook 04
```

O executor registra a duração de cada notebook em `execucao_notebooks.json`, numa pasta externa `diario/AAAA-MM-DD/`. O processamento completo envolve centenas de milhares de documentos; tempo e consumo de memória dependem do equipamento.

## Organização do projeto

```text
.
├── Page/                  # Landing page das quatro visualizações
├── configuracao/          # Fontes dos dados e decisões sobre conflitos de DOI
├── data/                  # Entradas e dados gerados localmente; fora do Git
├── notebooks/             # Seis etapas do fluxo principal
│   └── enriquecimento/    # Coletor original OpenAlex, separado do pipeline
├── outputs/
│   ├── amostras/          # HTMLs amostrados do LDA e do streamgraph
│   ├── completos/         # HTMLs completos do LDA e do streamgraph
│   └── tables/            # CSVs e registros gerados na execução local
├── src/                   # Configuração, processamento e exportação
├── .env.example
├── index.html             # Entrada do site, direciona para Page/
└── requirements.txt
```

Além dos quatro HTMLs, a execução local produz tokens, dicionários, corpora, modelos e métricas em `data/`. Os CSVs de autores em `outputs/tables/` incluem o ranking completo, os 15% selecionados, os 25 primeiros e a amostra de 50 mil nomes. 

## Critérios de análise

- **Texto e tópicos:** títulos e resumos passam por lematização com spaCy, remoção de stopwords, formação de bigramas e construção de bag of words. Ambos os LDAs usam Gensim, 20 tópicos, dez passagens e aprendizagem online em minilotes de até 2.000 documentos.
- **Autores:** cada par artigo × nome normalizado é contado uma vez. Cada coautor recebe uma publicação inteira; a soma das camadas representa autorias. Nomes são normalizados; grupos e instituições permanecem na base.
- **Período:** as séries do streamgraph têm três observações anuais, de 2020 a 2022. As curvas entre anos são interpolações visuais. O release de junho não cobre todo o ano de 2022.

Os parâmetros estão em [src/config.py](src/config.py), e os cinco grupos de DOI em conflito têm suas decisões documentadas em [configuracao/resolucoes_doi.csv](configuracao/resolucoes_doi.csv).

## Artefato de enriquecimento

O [notebook de coleta OpenAlex](notebooks/enriquecimento/01_coleta_openalex.ipynb)  está separado do fluxo principal e desativado por padrão (`EXECUTAR_CONSULTAS=False`). Nessa configuração, não envia requisições nem grava arquivos.

Esse artefato documenta a origem do enriquecimento. A execução dos seis notebooks utiliza o checkpoint já fornecido.
