# Configuração da replicação: LDA e publicações por nome de autor.
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)
DATA = Path(os.getenv('CORD19_DATA_DIR', ROOT / 'data')).resolve()
RAW = DATA / 'raw' / 'cord19_2022-06-02'
STAGED = DATA / 'staged'
CURATED = DATA / 'curated'
CHECKPOINTS = DATA / 'checkpoints'
RECOVERY = CHECKPOINTS / 'recuperacao_dados'
LDA_CHECKPOINTS = CHECKPOINTS / 'lda'
OUTPUTS = ROOT / 'outputs'
DOCS = ROOT / 'configuracao'
RELEASE = '2022-06-02'
YEAR_START, YEAR_END = 2020, 2022
DOI_PREFIX_PATTERN = r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)'
COLUMNS = ['cord_uid', 'doi', 'title', 'abstract', 'authors', 'publish_time']
# Marcadores padrão do read_csv, explícitos para preservar a leitura dos nulos.
NULL_VALUES = ['', '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN',
               '-NaN', '-nan', '1.#IND', '1.#QNAN', '<NA>', 'N/A', 'NA',
               'NULL', 'NaN', 'None', 'n/a', 'nan', 'null']
LDA_NUM_TOPICS = 20
LDA_SAMPLE_SIZE = 200_000
LDA_EXTRA_STOPWORDS = frozenset({
    'article', 'describe', 'discuss', 'examine', 'include', 'investigate',
    'need', 'paper', 'present', 'provide', 'relate', 'report', 'show',
    'study', 'suggest', 'use',
})
RANDOM_SEED = 42
TEXT_BATCH_SIZE = 1000
NO_BELOW, NO_ABOVE, KEEP_N = 20, 0.5, 100_000
LDA_PASSES, LDA_CHUNKSIZE = 10, 2000
PYLDAVIS_MDS = 'mmds'
AUTHOR_TOP_FRACTION = 0.15
AUTHOR_DEFAULT_VISIBLE = 25
AUTHOR_SAMPLE_SIZE = 50_000
AUTHOR_COLORS = (
    '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
    '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab',
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',
)


def ensure_directories():
    for path in [RAW, STAGED, CURATED / 'lda', CURATED / 'autores', DOCS,
                 OUTPUTS / 'completos', OUTPUTS / 'tables',
                 OUTPUTS / 'amostras',
                 RECOVERY, LDA_CHECKPOINTS,
                 STAGED / 'lda' / 'completo', STAGED / 'lda' / 'amostra',
                 CURATED / 'lda' / 'completo' / 'k20', CURATED / 'lda' / 'amostra' / 'k20']:
        path.mkdir(parents=True, exist_ok=True)


def metadata_path():
    path = Path(os.getenv('CORD19_METADATA', RAW / 'metadata.csv'))
    if not path.is_file():
        raise FileNotFoundError(
            f'metadata.csv ausente. Coloque o CSV do release {RELEASE} em {path} '
            'ou configure CORD19_METADATA. A exploração não inicia download automaticamente.')
    return path


# O enriquecimento usa somente o arquivo bibliográfico fornecido com os dados.
def enrichment_path():
    path = RECOVERY / 'checkpoint_enriquecimento.json'
    if not path.is_file():
        raise FileNotFoundError(f'Forneça o checkpoint de enriquecimento em {path}. Não são feitas consultas à API.')
    return path
