"""Execute the MT3 notebook in a fresh kernel using this Python interpreter.

Usage: python run_notebook.py
Optional short checks: --task task2 --steps 2 --batch-size 1 --eval-windows 2
Overrides apply only in memory; the source notebook is never modified.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', choices=['task1', 'task2'])
    parser.add_argument('--steps', type=int)
    parser.add_argument('--batch-size', type=int)
    parser.add_argument('--eval-windows', type=int)
    parser.add_argument('--output', default='MT3_Reproduction.executed.ipynb')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    notebook = nbformat.read(root / 'MT3_Reproduction.ipynb', as_version=4)
    substitutions = {}
    if args.task:
        substitutions["TASK = 'task1'"] = f"TASK = '{args.task}'"
    for argument, setting in [(args.steps, 'TRAIN_STEPS_OVERRIDE'),
                              (args.batch_size, 'BATCH_SIZE_OVERRIDE'),
                              (args.eval_windows, 'EVAL_WINDOWS_OVERRIDE')]:
        if argument is not None:
            substitutions[f'{setting} = None'] = f'{setting} = {argument}'
    for old, new in substitutions.items():
        matches = [cell for cell in notebook.cells if cell.cell_type == 'code' and old in cell.source]
        if len(matches) != 1:
            raise RuntimeError(f'Expected one parameter assignment: {old}')
        matches[0].source = matches[0].source.replace(old, new)

    def progress(cell, cell_index, **kwargs):
        if cell.cell_type == 'code':
            print(f'Executing code cell {cell_index + 1}/{len(notebook.cells)}', flush=True)

    with tempfile.TemporaryDirectory(prefix='mt3_notebook_') as temporary:
        temporary = Path(temporary)
        kernels = temporary / 'kernels'
        spec = kernels / 'mt3-python'
        spec.mkdir(parents=True)
        (spec / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Python MT3', 'language': 'python'}), encoding='utf-8')
        for key in ['IPYTHONDIR', 'MPLCONFIGDIR', 'JUPYTER_RUNTIME_DIR']:
            path = temporary / key.lower()
            path.mkdir()
            os.environ[key] = str(path)
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        manager = KernelManager(kernel_name='mt3-python',
            kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]))
        NotebookClient(notebook, km=manager, timeout=7200, allow_errors=False,
                       resources={'metadata': {'path': str(root)}},
                       on_cell_start=progress).execute()
    nbformat.validate(notebook)
    output = root / args.output
    nbformat.write(notebook, output)
    print('Completed:', output, flush=True)


if __name__ == '__main__':
    main()
