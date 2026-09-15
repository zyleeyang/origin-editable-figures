"""Create a native editable GO enrichment chart in an independent Origin instance.

Input: CSV/XLSX with GOterm, subgroup, Enrichment score columns.
No enrichment analysis, significance testing, filtering, or score transformation.
"""

import argparse
import hashlib
import importlib
import json
import math
import platform
import sys
from pathlib import Path

from origin_session import OwnedOrigin

GROUPS = (
    ('Biological process', 'BP', '#25A17C'),
    ('Cellular component', 'CC', '#D96622'),
    ('Molecular function', 'MF', '#6C73B2'),
)
REQUIRED = ('GOterm', 'subgroup', 'Enrichment score')


def read_data(path, sheet):
    import numpy as np
    import pandas as pd

    if path.suffix.lower() == '.csv':
        source = pd.read_csv(path, encoding='utf-8-sig', float_precision='round_trip')
    elif path.suffix.lower() == '.xlsx':
        source = pd.read_excel(path, sheet_name=sheet, engine='openpyxl')
    else:
        raise ValueError('Input must be a .csv or .xlsx file.')
    if not set(REQUIRED).issubset(source.columns):
        raise ValueError('Required columns: ' + ', '.join(REQUIRED))
    source = source.dropna(how='all').copy()
    source_rows = source.index.to_numpy() + 2
    source = source.loc[:, list(REQUIRED)].reset_index(drop=True)
    if source.empty or source.isna().any().any():
        raise ValueError('Required columns must contain complete, nonempty data.')
    for col in ('GOterm', 'subgroup'):
        if not source[col].map(lambda s: isinstance(s, str) and bool(s.strip())).all():
            raise ValueError(col + ' must contain nonempty text.')
    source['Enrichment score'] = pd.to_numeric(source['Enrichment score'], errors='raise')
    scores = source['Enrichment score'].to_numpy(float)
    if not np.isfinite(scores).all() or (scores < 0).any():
        raise ValueError('Enrichment scores must be finite and nonnegative.')
    if set(source.subgroup) != {name for name, _, _ in GROUPS}:
        raise ValueError('Expected all three subgroups: Biological process, Cellular component, Molecular function.')
    if source.duplicated(['subgroup', 'GOterm']).any():
        raise ValueError('Duplicate GOterm within the same subgroup; resolve before plotting.')
    # Preserve source row order within each group; group order follows BP, CC, MF.
    records = []
    position = 1
    for full, short, color in GROUPS:
        for i, row in source[source.subgroup == full].iterrows():
            records.append({'Position': position, 'GOterm': row.GOterm,
                            'subgroup': full, 'BP': math.nan, 'CC': math.nan,
                            'MF': math.nan, 'Source row': int(source_rows[i]),
                            'Tick label': '', short: float(row['Enrichment score'])})
            position += 1
        position += 1
    return source, pd.DataFrame(records)


def write_sheet(sheet, frame, axis):
    import pandas as pd
    sheet.from_df(frame)
    sheet.cols = len(frame.columns)
    sheet.cols_axis(axis)
    for i, column in enumerate(frame):
        if not pd.api.types.is_numeric_dtype(frame[column]):
            sheet.obj.Columns(i).SetTextAndNumericSetAlwaysAsText(True)
            sheet.from_list(i, frame[column].fillna('').astype(str).tolist(), lname=column)


def build(args, source, data):
    import numpy as np
    import pandas as pd

    if platform.system() != 'Windows':
        raise RuntimeError('Native Origin automation requires desktop Windows with Origin installed.')
    if args.dependency_path:
        sys.path.insert(0, str(args.dependency_path.resolve(strict=True)))
    try:
        op = importlib.import_module('originpro')
    except ImportError as exc:
        raise RuntimeError('Install requirements.txt into this Python environment, or use --dependency-path.') from exc

    out = args.output_dir.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError('Output directory must be new or empty: ' + str(out))
    out.mkdir(parents=True, exist_ok=True)
    check_dir = out / 'verification'
    check_dir.mkdir()
    target = out / 'go_enrichment.opju'
    source_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
    width, height = args.page_width, args.page_height
    left, top, plot_width, plot_height = width * .15, height * .05, width * .8, height * .45
    baseline, frame_bottom = height * .5, height * .95
    xmax = float(data.Position.max()) + 1
    max_score = float(source['Enrichment score'].max())
    ymax = args.y_max or max(.05, (math.floor(max_score * 20) + 1) / 20)
    if ymax < max_score:
        raise ValueError('--y-max would clip a data value.')
    y_step = args.y_step or max(0.1, float(math.ceil(ymax / 7)))
    metadata = {'source_file': args.input.name, 'source_sha256': source_hash,
                'records': len(data), 'statistics_recomputed': False,
                'group_order': ['BP', 'CC', 'MF'],
                'counts': {s: int((data.subgroup == full).sum()) for full, s, _ in GROUPS},
                'layout': {'width_mm': width, 'height_mm': height,
                           'label_rotation': args.rotation, 'label_size_pt': args.label_size}}

    def xy(x, y):
        return (x-left) / plot_width * xmax, ymax - (y-top) / plot_height * ymax

    def label(layer, name, content, x, y, size, color='#000000', bold=False, angle=0):
        obj = layer.add_label(r'\b(' + content + ')' if bold else content)
        obj.name = name
        obj.set_int('attach', 0)
        obj.set_int('font', op.lt_int('font(Arial)'))
        obj.set_float('fsize', size)
        obj.set_int('showframe', 0)
        obj.color = color
        obj.set_float('rotate', angle)
        xx, yy = xy(x, y)
        obj.set_float('x', xx)
        obj.set_float('y', yy)
        return obj

    def line(layer, name, x1, y1, x2, y2, color):
        a, b = xy(x1, y1)
        c, d = xy(x2, y2)
        obj = layer.add_line(a, b, c, d)
        obj.name, obj.color, obj.width = name, color, .55

    with OwnedOrigin(op, report=metadata, report_path=check_dir/'verification.json'):
        op.new()
        book = op.new_book('w', lname='GO enrichment data')
        book.name = 'GOData'
        raw = book[0]
        raw.name = 'Source'
        write_sheet(raw, source, 'NNY')
        for full, short, color in GROUPS:
            selected = data.subgroup == full
            data.loc[selected, 'Tick label'] = data.loc[selected, 'GOterm'].map(
                lambda term: rf'\c{op.ocolor(color)}({term})')
        w = book.add_sheet('PlotData')
        write_sheet(w, data, 'XNNYYYNN')
        w.set_str('tree.data.source', args.input.name)
        w.set_str('tree.data.source_sha256', source_hash)
        w.set_str('tree.data.note', 'Edit BP/CC/MF values to update the bars. Tick label controls displayed names and colors. Source is the original input snapshot. No enrichment analysis performed.')
        graph = op.new_graph(template='column', lname='GO enrichment')
        graph.name = 'GOEnrichment'
        graph.lt_exec(f'page.kar=0;page.width={width}/25.4*page.resx;page.height={height}/25.4*page.resy;page.aa=1;page.autosize=0;')
        layer = graph[0]
        layer.activate()
        layer.lt_exec(f'layer.fixed=1;layer.factor=1;layer.unit=4;layer.left={left};layer.top={top};layer.width={plot_width};layer.height={plot_height};layer.border=0;layer.showFrame=0;layer.maxpts=0;')
        for name in ['legend', 'xb', 'yl', 'xt', 'yr']:
            obj = layer.label(name)
            if obj:
                obj.remove()
        for k, (_, short, color) in enumerate(GROUPS):
            plot = layer.add_plot(w, 3+k, 0, type='c')
            plot.color = color
            plot.set_cmd(f'-pfb {op.ocolor(color)}', f'-pbc {op.ocolor(color)}',
                         '-pbw 0', f'-vg {args.bar_gap}', '-pfp 0')
        layer.set_xlim(0, xmax, 1)
        layer.set_ylim(0, ymax, y_step)
        for axis in ['x', 'y']:
            layer.lt_exec(f'layer.{axis}.showAxes=1;layer.{axis}.showLabels=1;layer.{axis}.showGrids=0;layer.{axis}.opposite=0;layer.{axis}.showopposite=0;layer.{axis}.ticks=2;layer.{axis}.minorTicks=0;layer.{axis}.ticklength=4.5;layer.{axis}.thickness=1.15;layer.{axis}.tickthickness=1.15;layer.{axis}.label.font=font(Arial);layer.{axis}.label.fsize=12;layer.{axis}.label.bold=1;layer.{axis}.label.rotate=0;layer.{axis}.label.wrap=0;layer.{axis}.rescale=1;')
        positions = data.Position.tolist()
        layer.set_str('x.ticksbydata', ' '.join(map(str, positions)))
        layer.set_int('x.labeltype', 2)
        layer.set_str('x.labeltext', w.obj.Columns(7).GetDatasetName())
        layer.lt_exec(f'layer.x.label.fsize={args.label_size};layer.x.label.rotate={args.rotation};layer.x.label.italic=1;layer.x.label.align=1;layer.x.label.offsetH=-55;layer.x.label.offsetV=-20;layer.y.label.decPlaces=-1;layer.y.label.offsetH=15;')
        label(layer, 'YTitle', 'Enrichment score', width*25/240, height*.275, 17.5, bold=True, angle=90)
        shift = (frame_bottom-baseline) / math.tan(math.radians(args.rotation))
        for full, short, color in GROUPS:
            pos = data.loc[data.subgroup == full, 'Position']
            a = left + (float(pos.min())-.42) / xmax * plot_width
            b = left + (float(pos.max())+.42) / xmax * plot_width
            line(layer, short+'FrameLeft', a, baseline, a-shift, frame_bottom, color)
            line(layer, short+'FrameRight', b, baseline, b-shift, frame_bottom, color)
            line(layer, short+'FrameBottom', a-shift, frame_bottom, b-shift, frame_bottom, color)
            label(layer, short+'Group', full, (a+b)/2-shift, height*176/180, 12, color)
        legend_text = '\n'.join(rf'\l({k+1}, Width:p85 Height:p55) {short}' for k, (_, short, _) in enumerate(GROUPS))
        label(layer, 'legend', legend_text, width*215.5/240, height*20/180, 12.5)
        graph.activate()
        if not op.save(str(target)):
            raise RuntimeError('Origin did not save the project.')
        op.new()
        if not op.open(str(target)):
            raise RuntimeError('Origin did not reopen the saved project.')
        graphs = list(op.pages('g'))
        assert len(graphs) == 1 and len(graphs[0]) == 1
        graph = graphs[0]
        layer = graph[0]
        assert len(layer.plot_list()) == 3
        actual_source = op.find_sheet('w', '[GOData]Source').to_df()
        pd.testing.assert_frame_equal(actual_source, source, check_dtype=False, check_names=False)
        actual = op.find_sheet('w', '[GOData]PlotData')
        back = actual.to_df()
        assert back.GOterm.tolist() == data.GOterm.tolist()
        assert back.subgroup.tolist() == data.subgroup.tolist()
        assert back['Tick label'].tolist() == data['Tick label'].tolist()
        assert back['Source row'].tolist() == data['Source row'].tolist()
        np.testing.assert_array_equal(back.Position, data.Position)
        for k, (_, short, color) in enumerate(GROUPS):
            np.testing.assert_array_equal(back[short].to_numpy(float), data[short].to_numpy(float))
            assert layer.plot_list()[k].obj.GetDatasetName() == actual.obj.Columns(k+3).GetDatasetName()
            assert tuple(layer.plot_list()[k].color) == tuple(int(color[i:i+2],16) for i in (1,3,5))
        assert [float(v) for v in layer.get_str('x.ticksbydata').split()] == positions
        assert layer.get_str('x.labeltext').split('"')[0] == '[GOData]PlotData!H'
        graph.activate()
        preview = out / 'go_enrichment.png'
        if not graph.save_fig(str(preview), width=args.preview_width) or not preview.is_file():
            raise RuntimeError('Origin preview export failed.')
        assert hashlib.sha256(args.input.read_bytes()).hexdigest() == source_hash
        metadata.update(reopened=True, data_and_label_mapping_verified=True,
                        graph_pages=1, layers=1, native_column_series=3,
                        source_unchanged=True, origin_version=op.lt_float('@V'),
                        visual_review='Inspect go_enrichment.png, especially after changing label lengths or group sizes.')
        print('Saved and reopened: ' + str(target), flush=True)
    print('Origin closed; verification complete.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--sheet', default=0, help='Excel sheet name; defaults to first sheet.')
    parser.add_argument('--dependency-path', type=Path, help='Optional parent directory containing originpro.')
    parser.add_argument('--validate-only', action='store_true', help='Check input data without starting Origin.')
    parser.add_argument('--page-width', type=float, default=240, help='Page width in mm.')
    parser.add_argument('--page-height', type=float, default=180, help='Page height in mm.')
    parser.add_argument('--label-size', type=float, default=8.7, help='X label size in points.')
    parser.add_argument('--rotation', type=float, default=74, help='X label rotation, 60 to 90 degrees.')
    parser.add_argument('--bar-gap', type=float, default=30, help='Origin gap percentage, 0 to 100.')
    parser.add_argument('--y-max', type=float)
    parser.add_argument('--y-step', type=float)
    parser.add_argument('--preview-width', type=int, default=2400)
    args = parser.parse_args()
    args.input = args.input.resolve(strict=True)
    for value in [args.page_width, args.page_height, args.label_size, args.preview_width]:
        if not math.isfinite(value) or value <= 0:
            parser.error('Page, font and preview dimensions must be finite and positive.')
    if not 60 <= args.rotation <= 90 or not 0 <= args.bar_gap <= 100:
        parser.error('Rotation must be 60..90 degrees; bar gap must be 0..100.')
    for value in (args.y_max, args.y_step):
        if value is not None and (not math.isfinite(value) or value <= 0):
            parser.error('Y limits and step must be finite and positive.')
    source, data = read_data(args.input, args.sheet)
    if args.validate_only:
        print(json.dumps({'rows': len(data), 'groups': source.groupby('subgroup', sort=False).size().to_dict()}, ensure_ascii=False))
        return
    if not args.output_dir:
        parser.error('--output-dir is required unless --validate-only is used.')
    build(args, source, data)


if __name__ == '__main__':
    main()
