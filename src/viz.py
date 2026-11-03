# Exportação dos streamgraphs anual e mensal, com D3 e dados incorporados.
import json
from pathlib import Path

from . import config as cfg


# Incorpora D3 e dados no HTML para abertura sem internet.
def write_streamgraph(payload):
    encoded = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).translate(
        {ord('<'): r'\u003c', ord('>'): r'\u003e', ord('&'): r'\u0026'})
    assets = Path(__file__).parent / 'assets'
    template = (assets / 'streamgraph.html').read_text(encoding='utf-8')
    d3 = (assets / 'd3.v7.min.js').read_text(encoding='utf-8')
    folder = cfg.OUTPUTS / 'visualizations'
    folder.mkdir(parents=True, exist_ok=True)
    name = 'streamgraph_autores_mensal.html' if payload['granularidade'] == 'mensal' else 'streamgraph_autores.html'
    path = folder / name
    path.write_text(template.replace('__DATA__', encoded).replace('__D3__', d3), encoding='utf-8')
    return path


# Monta as contagens por período dos nomes escolhidos e exporta o streamgraph.
def export_author_streamgraph(authors, counts, methodology, monthly=False):
    periods = ([f'{year}-{month:02d}' for year in range(cfg.YEAR_START, cfg.YEAR_END + 1) for month in range(1, 13)]
               if monthly else [str(year) for year in range(cfg.YEAR_START, cfg.YEAR_END + 1)])
    series = counts.pivot(index='autor_chave', columns='periodo', values='publicacoes').reindex(
        index=authors['autor_chave'], columns=periods).fillna(0).astype('int64')
    rows = [{'id': row.autor_id, 'nome': row.autor_nome, 'posicao': int(row.posicao),
             'total': int(row.publicacoes_total), 'com_mes': int(row.publicacoes_com_mes),
             'sem_mes': int(row.publicacoes_sem_mes), 'disponivel': True, 'serie': values.tolist()}
            for row, values in zip(authors.itertuples(index=False), series.to_numpy())]
    description = ('15% dos nomes com mais publicações no corpus textual atual. '
                   'Uma publicação inteira por nome e artigo; sem desambiguação de pessoas. '
                   'Inclui instituições e grupos. Séries anuais incluem publicações sem mês conhecido.')
    if monthly:
        description = '15% mais produtivos por contribuições com mês conhecido; contribuições sem mês são excluídas.'
    payload = {'tipo': 'autores', 'granularidade': 'mensal' if monthly else 'anual', 'itens': rows,
               'periodos': periods, 'padrao': cfg.AUTHOR_DEFAULT_VISIBLE, 'cores': cfg.AUTHOR_COLORS,
               'descricao': description, 'titulo': 'Publicações por nome de autor' + (' — mensal' if monthly else ''),
               'eixo_x': 'Mês de publicação do artigo' if monthly else 'Ano de publicação do artigo', 'metodologia': methodology}
    return write_streamgraph(payload)
