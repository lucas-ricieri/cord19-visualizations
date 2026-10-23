# Transformações bibliográficas; a sequência de preparação está nos notebooks 01–03.
import pandas as pd

from . import config as cfg


# Preenche somente os campos ausentes com as respostas bibliográficas fornecidas.
def apply_metadata_checkpoint(incomplete, checkpoint):
    records = [{'doi': doi, **{col: value.get(col) for col in cfg.COLUMNS[2:]}}
               for doi, value in checkpoint.items() if value.get('_status') == 'sucesso']
    response = pd.DataFrame(records, columns=cfg.COLUMNS[1:])
    result = incomplete.merge(response, on='doi', how='left', validate='many_to_one',
                              sort=False, suffixes=('', '_api'))
    for column in cfg.COLUMNS[2:]:
        result[column] = result[column].fillna(result[f'{column}_api'])
    result = result[cfg.COLUMNS]
    return result.mask(result.isin(cfg.NULL_VALUES))



# Normaliza DOI e interpreta datas sem inventar mês ou dia.
def normalize_bibliography(frame):
    result = frame.copy()
    result['doi_normalizado'] = result['doi'].str.strip().str.lower().str.replace(
        cfg.DOI_PREFIX_PATTERN, '', regex=True)
    text = result['publish_time'].str.strip()
    annual = text.str.fullmatch(r'\d{4}', na=False)
    dates = pd.to_datetime(text.where(text.str.fullmatch(r'\d{4}-\d{2}-\d{2}', na=False)),
                           format='%Y-%m-%d', errors='coerce')
    result['data_publicacao'] = dates
    result['ano_publicacao'] = dates.dt.year.where(~annual, pd.to_numeric(text.where(annual))).astype('Int32')
    result['precisao_data'] = 'invalida'
    result.loc[dates.notna(), 'precisao_data'] = 'dia'
    result.loc[annual, 'precisao_data'] = 'ano'
    result['doi_valido'] = result['doi_normalizado'].str.fullmatch(r'10\.\d{4,9}/\S+', na=False)
    return result



def resolve_doi_conflicts(full, resolutions):
    if resolutions is not None:
        chosen = resolutions.rename(columns={'cord_uid': 'representante'})
        check = chosen.merge(full[['doi_normalizado', 'cord_uid']], left_on=['doi_normalizado', 'representante'],
                             right_on=['doi_normalizado', 'cord_uid'], how='left', indicator=True)
        if check['_merge'].ne('both').any():
            raise ValueError('Uma resolução de DOI aponta para um cord_uid ausente ou com outro DOI.')
        mapped = full.merge(chosen, on='doi_normalizado', how='left', validate='many_to_one', sort=False)
        mapped['representante'] = mapped['representante'].fillna(mapped['cord_uid'])
        return mapped.loc[mapped['cord_uid'].eq(mapped['representante'])].drop(columns=['representante', 'motivo'])
    return full



# Seleciona os anos do período definido na configuração.
def filter_period(frame):
    return frame.loc[frame['ano_publicacao'].between(cfg.YEAR_START, cfg.YEAR_END)].reset_index(drop=True)
