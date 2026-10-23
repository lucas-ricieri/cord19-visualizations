# Normalização das autorias; contagens, ranking e sorteio estão no notebook 05.
import pandas as pd

from . import config as cfg


# Separa nomes por ponto e vírgula e mantém uma autoria por nome e artigo.
def split_authors(frame):
    result = frame[['cord_uid', 'authors', 'ano_publicacao', 'data_publicacao', 'precisao_data']].copy()
    dates = pd.to_datetime(result['data_publicacao'].where(result['precisao_data'].eq('dia')), errors='coerce')
    result['periodo_mensal'] = dates.dt.strftime('%Y-%m').astype('string')
    result['nome_original'] = result.pop('authors').str.split(';')
    result = result.explode('nome_original', ignore_index=True)
    result['nome_original'] = result['nome_original'].astype('string').str.normalize('NFC').str.replace(
        r'\s+', ' ', regex=True).str.strip()
    result['autor_chave'] = result['nome_original'].str.casefold()
    valid = result['nome_original'].notna() & ~result['nome_original'].isin(cfg.NULL_VALUES)
    result = result.loc[valid].drop_duplicates(['cord_uid', 'autor_chave']).copy()
    result['ano_publicacao'] = result['ano_publicacao'].astype('int32')
    return result[['cord_uid', 'autor_chave', 'nome_original', 'ano_publicacao', 'periodo_mensal']]
