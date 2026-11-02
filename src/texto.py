# Leitura de tokens, lematização em blocos e gravação do corpus atual.
import hashlib
import os

# Carrega o runtime C++ distribuído pelo scikit-learn no Windows.
if os.name == 'nt':
    import sklearn

from gensim.corpora import Dictionary, MmCorpus
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import spacy

from . import config as cfg
from .io_utils import atomic_json, atomic_parquet


# Localiza os dados e o modelo do corpus completo.
def lda_paths():
    return cfg.STAGED / 'lda' / 'completo', cfg.CURATED / 'lda' / 'completo' / 'k20'


# Lê os tokens em blocos e aplica os bigramas quando fornecidos.
def token_records(path, phrases=None):
    for batch in pq.ParquetFile(path).iter_batches(batch_size=1000):
        for row in batch.to_pylist():
            words = row['tokens']
            yield row['cord_uid'], phrases[words] if phrases is not None else words


# Lematiza título e resumo com os filtros linguísticos usados no projeto.
def lemmatize(texts, nlp):
    return [[token.lemma_.lower() for token in doc
             if token.pos_ in {'NOUN', 'ADJ', 'VERB', 'ADV'}
             and token.is_alpha and not token.is_stop and len(token.lemma_) > 2
             and token.lemma_.lower() not in cfg.LDA_EXTRA_STOPWORDS]
            for doc in nlp.pipe(texts, batch_size=64, n_process=1)]


# Junta os blocos concluídos, registra vazios e cria a ordem dos documentos atuais.
def combine_token_batches(parts, destination):
    schema = pa.schema([('cord_uid', pa.string()), ('tokens', pa.list_(pa.string()))])
    temporary = destination.with_suffix('.tmp.parquet')
    ids, empty = [], []
    with pq.ParquetWriter(temporary, schema, compression='zstd') as writer:
        for path in parts:
            frame = pd.read_parquet(path)
            valid = frame['tokens'].map(len).gt(0)
            ids.extend(frame.loc[valid, 'cord_uid'])
            empty.extend(frame.loc[~valid, 'cord_uid'])
            writer.write_table(pa.Table.from_pandas(frame.loc[valid], schema=schema, preserve_index=False))
    temporary.replace(destination)
    atomic_parquet(cfg.STAGED / '06_ordem_documentos.parquet',
                   pd.DataFrame({'doc_index': range(len(ids)), 'cord_uid': pd.Series(ids, dtype='string')}))
    atomic_parquet(cfg.STAGED / '05_documentos_vazios.parquet',
                   pd.DataFrame({'cord_uid': pd.Series(empty, dtype='string')}))
    return {'documentos': len(ids), 'vazios': len(empty), 'stopwords_adicionais': sorted(cfg.LDA_EXTRA_STOPWORDS)}


# Processa o corpus curado; checkpoints permitem retomar blocos após interrupção.
def preprocess(batch_size=cfg.TEXT_BATCH_SIZE, progress=None):
    cfg.ensure_directories()
    source = cfg.STAGED / '04_corpus_periodo.parquet'
    nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
    with source.open('rb') as stream:
        content = hashlib.file_digest(stream, 'sha256').hexdigest()
    settings = (content, batch_size, nlp.meta['version'], sorted(cfg.LDA_EXTRA_STOPWORDS))
    checkpoint = cfg.LDA_CHECKPOINTS / hashlib.sha256(repr(settings).encode()).hexdigest()[:12]
    checkpoint.mkdir(parents=True, exist_ok=True)
    parquet = pq.ParquetFile(source)
    parts, done = [], 0
    for index, batch in enumerate(parquet.iter_batches(batch_size=batch_size, columns=['cord_uid', 'title', 'abstract'])):
        path = checkpoint / f'lote_{index:06d}.parquet'
        if not path.exists():
            frame = batch.to_pandas()
            tokens = lemmatize((frame['title'] + ' ' + frame['abstract']).tolist(), nlp)
            atomic_parquet(path, pd.DataFrame({'cord_uid': frame['cord_uid'], 'tokens': tokens}))
        parts.append(path)
        done += batch.num_rows
        if progress:
            progress('lematizacao', done, parquet.metadata.num_rows)
    result = combine_token_batches(parts, cfg.STAGED / '05_tokens.parquet')
    atomic_json(cfg.STAGED / '05_preprocessamento.json', result)
    return result


# Produz um vetor por vez e registra quais IDs têm termos no dicionário.
def bow_records(source, dictionary, phrases, kept, omitted):
    for uid, words in token_records(source, phrases):
        bow = dictionary.doc2bow(words)
        if bow:
            kept.append(uid)
            yield bow
        else:
            omitted.append(uid)


# Grava o BOW e os IDs na mesma ordem, mantendo o corpus no disco.
def save_corpus(dictionary, phrases):
    folder, _ = lda_paths()
    folder.mkdir(parents=True, exist_ok=True)
    source = cfg.STAGED / '05_tokens.parquet'
    kept, omitted = [], []
    path = folder / '06_corpus.mm'
    MmCorpus.serialize(str(path), bow_records(source, dictionary, phrases, kept, omitted))
    atomic_parquet(folder / '06_ordem_documentos.parquet',
                   pd.DataFrame({'doc_index': range(len(kept)), 'cord_uid': pd.Series(kept, dtype='string')}))
    atomic_parquet(folder / '06_documentos_sem_vocabulario.parquet',
                   pd.DataFrame({'cord_uid': pd.Series(omitted, dtype='string')}))
    atomic_json(folder / '06_parametros.json', {'documentos': len(kept), 'vocabulario': len(dictionary),
                'descartados_sem_vocabulario': len(omitted), 'no_below': cfg.NO_BELOW,
                'no_above': cfg.NO_ABOVE, 'keep_n': cfg.KEEP_N})
    return MmCorpus(str(path))


# Carrega somente o dicionário e o BOW do conjunto atual solicitado.
def load_dictionary_and_corpus():
    folder, _ = lda_paths()
    return Dictionary.load(str(folder / '06_dicionario.dict')), MmCorpus(str(folder / '06_corpus.mm'))


# Registra métricas e termos dos vinte tópicos do modelo atual.
def save_lda_results(model, dictionary, corpus):
    _, folder = lda_paths()
    folder.mkdir(parents=True, exist_ok=True)
    model.save(str(folder / 'modelo_k20.model'))
    terms = [{'topico': topic, 'termos': ', '.join(word for word, _ in model.show_topic(topic, topn=10)),
              'rotulo_manual': ''} for topic in range(cfg.LDA_NUM_TOPICS)]
    pd.DataFrame(terms).to_csv(folder / 'topicos_rotulos.csv', index=False)
    metrics = {'num_topics': cfg.LDA_NUM_TOPICS, 'passes': cfg.LDA_PASSES,
               'random_state': cfg.RANDOM_SEED, 'documentos': len(corpus), 'vocabulario': len(dictionary),
               'stopwords_adicionais': sorted(cfg.LDA_EXTRA_STOPWORDS),
               'log_perplexity': float(model.log_perplexity(corpus))}
    atomic_json(folder / 'metricas.json', metrics)
    return metrics
