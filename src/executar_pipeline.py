# Executa os notebooks na sequência, usando o mesmo Python do terminal.
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

from . import config as cfg


# Executa uma narrativa e salva as tabelas exibidas no próprio notebook.
def execute_notebook(path, reprocess=False):
    notebook = nbformat.read(path, as_version=4)
    if reprocess:
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                cell.source = cell.source.replace('REPROCESSAR = False', 'REPROCESSAR = True')
    manager = KernelManager(kernel_name='python3')
    manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
    client = NotebookClient(notebook, km=manager, timeout=None,
                            resources={'metadata': {'path': str(cfg.ROOT)}},
                            on_cell_start=lambda cell, cell_index: print(f'  Célula {cell_index + 1}/{len(notebook.cells)}', flush=True))
    try:
        client.execute(cleanup_kc=True)
    finally:
        # O controle de reprocessamento volta ao padrão ao salvar o notebook.
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                cell.source = cell.source.replace('REPROCESSAR = True', 'REPROCESSAR = False')
        nbformat.write(notebook, path)


# Cronometra cada notebook e guarda o registro fora da pasta principal do código.
def main():
    parser = argparse.ArgumentParser(description='Executa os cinco notebooks do bruto às duas visualizações HTML.')
    parser.add_argument('--notebook', help='Executa somente o notebook com este prefixo, por exemplo 04.')
    parser.add_argument('--reprocessar', action='store_true', help='Refaz lemas, corpus e modelos; mantém checkpoints dos lemas.')
    args = parser.parse_args()
    cfg.metadata_path()
    cfg.enrichment_path()
    reports = cfg.ROOT.parents[1] / 'diario' / datetime.now().strftime('%Y-%m-%d')
    reports.mkdir(parents=True, exist_ok=True)
    report = reports / 'execucao_notebooks.json'
    stages = []
    notebooks = sorted((cfg.ROOT / 'notebooks').glob(f'{args.notebook or ""}*.ipynb'))
    if not notebooks:
        parser.error('Nenhum notebook corresponde ao prefixo informado.')
    for path in notebooks:
        started = time.perf_counter()
        item = {'notebook': path.name, 'estado': 'em execução'}
        stages.append(item)
        report.write_text(json.dumps(stages, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Executando {path.name}', flush=True)
        try:
            execute_notebook(path, args.reprocessar)
            item['estado'] = 'concluído'
        except Exception as error:
            item.update(estado='falhou', erro=str(error))
            raise
        finally:
            item['segundos'] = time.perf_counter() - started
            report.write_text(json.dumps(stages, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"{path.name}: {item['estado']} em {item['segundos']:.1f} s", flush=True)


if __name__ == '__main__':
    main()
