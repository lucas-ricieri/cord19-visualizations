# Normalização das autorias; contagens, ranking e sorteio estão no notebook 05.
import re

import pandas as pd

from . import config as cfg


# Identifica sinais de autoria coletiva sem exigir vírgula ou sobrenome em nomes pessoais.
def is_collective_author(names):
    names = names.str.strip(' ,.')
    known_entities = {
        'ieee', 'elsevier', 'springer nature', 'springer medizin', 'wiley', 'mdpi',
        'bohn stafleu van loghum', 'huisarts en wetenschap', 'astronomy',
        'china cdc weekly', 'bmj, india correspondent', 'ricors2040',
    }
    organization = re.compile(
        r'\b(?:consorti(?:um|a)|consórcio|collaborati(?:on|ve)|collaborators|colaboração|'
        r'universit\w*|universidad\w*|institut\w*|akademie)\b|'
        r'\b(?:working group|study group|research group|publishing group|'
        r'grupo de (?:pesquisa|estudo|trabalho)|groupe de travail|'
        r'task force|working party|editorial (?:board|office|staff|team)|'
        r'production office|multicenter study|on behalf of|'
        r'hospital (?:of|de|da|do)|cent(?:er|re) for|society of|'
        r'study investigators|research forum|science team|covid[- ]?19)\b|'
        r'\b(?:group|team|committee|society|association|foundation|network|'
        r'academy|initiative|agency|laborator(?:y|ies)|investigators|editors|staff)\s*$|'
        r'^(?:group|team|committee|network|study group|editors|project|initiative|investigators),|'
        r'\b(?:world health organization|centers? for disease control|'
        r'organização mundial da saúde|ministry of|department of|school of)\b|'
        r'^(?:the lancet|the plos|the bmj|cdc covid|covid[- ]?19)\b|'
        r'\b(?:ltd|llc|inc|gmbh|corp)\.?$'
    )
    return names.isin(known_entities) | names.str.contains(organization, na=False)


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
