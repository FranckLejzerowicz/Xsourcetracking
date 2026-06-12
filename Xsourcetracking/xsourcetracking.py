# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import sys
import subprocess

from Xsourcetracking.filter import get_filtered
from Xsourcetracking.utils import (
    get_metadata,
    get_params,
    get_dir_out,
    check_input_table,
    get_rarefaction,
    write_data_table
)
from Xsourcetracking.sourcesink import get_sourcesink
from Xsourcetracking.feast import run_feast
from Xsourcetracking.sourcetracker import run_sourcetracker
from Xsourcetracking.metastorms import run_metastorms
from Xsourcetracking.q2classifier import run_q2classifier


def xsourcetracking(
        i_table: str,
        o_dir: str,
        m_metadata: str,
        p_column: str,
        p_column_value: tuple,
        p_column_quant: int,
        p_filter_prevalence: float,
        p_filter_abundance: float,
        p_filter_order: str,
        p_column_name: str,
        p_sources: tuple,
        p_sink: str,
        p_method: str,
        p_cpus: int,
        p_chunks: int,
        p_st2_config: str,
        verbose: bool):

    # read the config passed woith all per-tool options
    params = get_params(p_st2_config)

    # check and read input table
    i_table, tab = check_input_table(i_table, verbose)

    # read metadata and collect sink / sources
    meta, col_name, sources, sink = get_metadata(
        m_metadata, p_column_name, p_sources, p_sink, verbose, p_method)

    # filter for command line params
    tab, o_dir = get_filtered(
        p_column, p_column_value, p_filter_prevalence, p_filter_abundance,
        p_filter_order, p_column_quant, tab, meta, o_dir)

    # filter for min rarefaction depth
    tab, raref = get_rarefaction(tab, params)

    # subset metadata to filtered samples
    meta = meta.set_index('sample_name').loc[tab.columns.tolist(), [col_name]]

    # get list of samples per sink / sources
    samples, counts, sources = get_sourcesink(meta, col_name, sink, sources)

    if len(counts) == 1:
        print('Not enough source(s) samples')
        sys.exit(0)

    # create the output folder
    dir_out = get_dir_out(o_dir, col_name, sink, sources, p_sources, p_method)

    # write data to be used
    tab_out = write_data_table(tab, dir_out, samples, raref, p_method)

    if p_method == 'feast':
        print('Preparing for sourcetracking using FEAST!')
        cmd = run_feast(
            tab_out,
            dir_out,
            samples,
            counts,
            sources,
            sink,
            p_chunks,
            params,
        )
    elif p_method == 'sourcetracker':
        print('Preparing for sourcetracking using Sourcetracker2!')
        cmd = run_sourcetracker(
            tab_out,
            dir_out,
            samples,
            counts,
            sources,
            sink,
            p_chunks,
            p_cpus,
            params
        )
    elif p_method == 'q2_classifier':
        print('Preparing for sourcetracking using QIIME2 sample-classifier!')
        cmd = run_q2classifier(
            tab_out,
            dir_out,
            samples,
            counts,
            sources,
            sink,
            p_chunks,
            p_cpus,
            params
        )
    elif p_method == 'metastorms':
        cmd = run_metastorms(
            tab_out,
            dir_out,
            samples,
            counts,
            sources,
            sink,
            p_chunks,
            p_cpus,
            params
        )

    script = '%s/cmd_%s.sh' % (dir_out, p_method)
    sh = open(script, 'w')
    sh.write('%s\n' % cmd)
    sh.close()
    print('Written:', script)
    if params['run']:
        print(cmd)
        subprocess.call(['sh', script])