"""Extract existing Origin graph pages into separate OPJU files.

Requires desktop Windows Origin and originpro. Keeps every non-graph page to
avoid guessing worksheet/formula dependencies. Does not flatten layers or refit.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from origin_session import OwnedOrigin

sys.dont_write_bytecode = True


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def graph_state(graph):
    """Snapshot structure/bindings and axis geometry, not all possible styles."""
    layers = []
    for layer in graph:
        layers.append({
            'datasets': [p.obj.GetDatasetName() for p in layer.plot_list()],
            'geometry': {prop: layer.get_float(prop) for prop in
                         ['x.from', 'x.to', 'y.from', 'y.to', 'left', 'top', 'width', 'height']},
            'show_frame': layer.get_int('showFrame'),
        })
    return layers


def worksheet_state(op):
    return {(book.name, sheet.name): sheet.to_df()
            for book in op.pages('w') for sheet in book}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--graphs', nargs='+', required=True,
                        help='Existing short graph-page names, not display titles')
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='New or empty folder; existing results are never overwritten')
    parser.add_argument('--dependency-path', type=Path,
                        help='Optional directory containing the originpro package')
    parser.add_argument('--previews', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output_dir.resolve()
    if source.suffix.lower() not in ('.opju', '.opj'):
        parser.error('Source must be an OPJU or OPJ project.')
    if len(set(n.casefold() for n in args.graphs)) != len(args.graphs):
        parser.error('Graph names must be unique.')
    for name in args.graphs:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
            parser.error('Use the actual alphanumeric short graph name: ' + name)
        if name.upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}:
            parser.error('Graph name is a reserved Windows filename: ' + name)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error('Output directory must be new or empty.')
    if args.dependency_path:
        sys.path.insert(0, str(args.dependency_path.resolve(strict=True)))
    import originpro as op
    import numpy as np
    import pandas as pd

    before = sha256(source)
    report = {'source': str(source), 'source_sha256': before,
              'retention': 'All non-graph pages retained; external links not audited.',
              'outputs': []}
    verification = output / 'verification'
    with OwnedOrigin(op, report=report, report_path=verification/'extraction.json'):
        op.new()
        if not op.open(str(source)):
            raise RuntimeError('Origin could not open the source project.')
        available = {g.name for g in op.pages('g')}
        missing = set(args.graphs) - available
        if missing:
            raise ValueError('Graph pages not found: ' + ', '.join(sorted(missing)))
        original_graphs = {name: graph_state(op.find_graph(name)) for name in args.graphs}
        original_worksheets = worksheet_state(op)
        output.mkdir(parents=True, exist_ok=True)
        verification.mkdir()
        for index, name in enumerate(args.graphs):
            if index:
                op.new()
                if not op.open(str(source)):
                    raise RuntimeError('Could not reopen source for ' + name)
            for graph in list(op.pages('g')):
                if graph.name != name:
                    graph.destroy()
            for page in list(op.pages()):
                page.activate()
                op.lt_exec('win -i;')
            graph = op.find_graph(name)
            graph.activate()
            op.lt_exec('win -z;')
            target = output / (name + '.opju')
            if target.exists():
                raise FileExistsError(target)
            if not op.save(str(target)):
                raise RuntimeError('Could not save ' + str(target))
            saved_hash = sha256(target)
            op.new()
            if not op.open(str(target)):
                raise RuntimeError('Could not reopen ' + str(target))
            assert [g.name for g in op.pages('g')] == [name]
            assert op.find_graph().name == name
            actual_graph = graph_state(op.find_graph(name))
            expected_graph = original_graphs[name]
            assert len(actual_graph) == len(expected_graph)
            for actual, expected in zip(actual_graph, expected_graph):
                assert actual['datasets'] == expected['datasets']
                assert actual['show_frame'] == expected['show_frame']
                for prop in expected['geometry']:
                    np.testing.assert_allclose(actual['geometry'][prop], expected['geometry'][prop],
                                               rtol=1e-12, atol=1e-10, equal_nan=True)
            worksheets = worksheet_state(op)
            assert worksheets.keys() == original_worksheets.keys()
            for key, expected in original_worksheets.items():
                pd.testing.assert_frame_equal(worksheets[key], expected, check_exact=True)
            if args.previews:
                preview = verification / (name + '.png')
                if not op.find_graph(name).save_fig(str(preview), width=1200):
                    raise RuntimeError('Preview export failed: ' + str(preview))
                assert preview.is_file() and preview.stat().st_size > 0
            assert sha256(target) == saved_hash
            report['outputs'].append({
                'file': target.name, 'sha256': saved_hash,
                'layers': len(actual_graph),
                'plots_per_layer': [len(x['datasets']) for x in actual_graph],
                'worksheet_count': len(worksheets), 'reopened': True,
                'worksheet_values_exact': True, 'plot_bindings_and_axes_verified': True,
                'full_style_or_external_link_verification': 'Not performed by this helper.',
            })
            print('Saved and verified: ' + str(target), flush=True)
        assert sha256(source) == before, 'Source file changed during extraction.'
        report['source_unchanged'] = True
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
