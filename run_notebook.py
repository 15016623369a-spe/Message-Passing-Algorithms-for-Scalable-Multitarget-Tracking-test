"""Execute the self-contained notebook without changing its clean source file.

Usage: python run_notebook.py [--quick]
The executed notebook and generated experiment files are saved under results/.
"""
from pathlib import Path
import argparse
import json
import os
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true', help='30 steps and 500 particles; environment check only')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    notebook = nbformat.read(root / 'MTT_BP_Python.ipynb', as_version=4)
    if args.quick:
        changed = 0
        for cell in notebook.cells:
            if cell.cell_type == 'code' and 'QUICK_CHECK = False' in cell.source:
                cell.source = cell.source.replace('QUICK_CHECK = False', 'QUICK_CHECK = True')
                changed += 1
        if changed != 1:
            raise RuntimeError('Expected exactly one QUICK_CHECK setting.')
    with tempfile.TemporaryDirectory(prefix='bp_notebook_') as temporary:
        temporary = Path(temporary)
        directory = temporary / 'kernels/bp-python'
        directory.mkdir(parents=True)
        (directory / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Python BP', 'language': 'python'}), encoding='utf-8')
        for key in ['IPYTHONDIR', 'MPLCONFIGDIR', 'JUPYTER_RUNTIME_DIR']:
            local = temporary / key.lower()
            local.mkdir()
            os.environ[key] = str(local)
        manager = KernelManager(kernel_name='bp-python',
            kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(directory.parent)]))
        NotebookClient(notebook, km=manager, timeout=1200, allow_errors=False,
                       resources={'metadata': {'path': str(root)}}).execute()
    nbformat.validate(notebook)
    output = root / 'results/MTT_BP_Python.executed.ipynb'
    output.parent.mkdir(exist_ok=True)
    nbformat.write(notebook, output)
    print('Completed:', output)
    print('Experiment files:', output.parent)


if __name__ == '__main__':
    main()
