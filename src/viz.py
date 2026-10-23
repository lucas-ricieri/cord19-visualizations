# Exportação do streamgraph anual em HTML, com D3 e dados incorporados.
import json
from pathlib import Path

from . import config as cfg


# Incorpora D3 e dados no HTML para abertura sem internet.
def write_streamgraph(payload, sample=False):
    encoded = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).translate(
        {ord('<'): r'\u003c', ord('>'): r'\u003e', ord('&'): r'\u0026'})
    assets = Path(__file__).parent / 'assets'
    template = (assets / 'streamgraph.html').read_text(encoding='utf-8')
    d3 = (assets / 'd3.v7.min.js').read_text(encoding='utf-8')
    folder = cfg.OUTPUTS / ('amostras' if sample else 'completos')
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'streamgraph_autores.html'
    path.write_text(template.replace('__DATA__', encoded).replace('__D3__', d3), encoding='utf-8')
    return path


# Monta as três contagens anuais dos nomes escolhidos e exporta o streamgraph.
def export_author_streamgraph(authors, annual, methodology, sample=False):
    periods = [str(year) for year in range(cfg.YEAR_START, cfg.YEAR_END + 1)]
    series = annual.pivot(index='autor_chave', columns='periodo', values='publicacoes').reindex(
        index=authors['autor_chave'], columns=periods).fillna(0).astype('int64')
    rows = [{'id': row.autor_id, 'nome': row.autor_nome, 'posicao': int(row.posicao),
             'total': int(row.publicacoes_total), 'com_mes': int(row.publicacoes_com_mes),
             'sem_mes': int(row.publicacoes_sem_mes), 'disponivel': True, 'serie': values.tolist()}
            for row, values in zip(authors.itertuples(index=False), series.to_numpy())]
    description = ('15% dos nomes com mais publicações no corpus textual atual. '
                   'Uma publicação inteira por nome e artigo; sem desambiguação de pessoas. '
                   'Inclui instituições e grupos. Séries anuais incluem publicações sem mês conhecido.')
    if sample:
        description = (f'Amostra aleatória de {len(authors):,} nomes dos 15% mais produtivos, '
                       f'sem reposição e com seed {cfg.RANDOM_SEED}. Contagens completas dos nomes sorteados. ' + description)
    payload = {'tipo': 'autores', 'granularidade': 'anual', 'amostra': sample, 'itens': rows,
               'periodos': periods, 'padrao': cfg.AUTHOR_DEFAULT_VISIBLE, 'cores': cfg.AUTHOR_COLORS,
               'descricao': description, 'titulo': 'Publicações por nome de autor — ' + ('amostra' if sample else 'completo'),
               'eixo_x': 'Ano de publicação do artigo', 'metodologia': methodology}
    return write_streamgraph(payload, sample)
