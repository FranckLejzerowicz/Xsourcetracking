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
    check_input_table,
    get_o_dir_paths,
    get_rarefaction,
    write_data_table
)
from Xsourcetracking.sourcesink import get_sourcesink_dict

from Xsourcetracking.feast import run_feast
from Xsourcetracking.sourcetracker import run_sourcetracker
from Xsourcetracking.classify import run_classify
from Xsourcetracking.metastorms import run_metastorms
from Xsourcetracking.q2classifier import run_q2classifier


def xsourcetracking(
        i_table: str,
        o_dir_path: str,
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
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_method: str,
        p_cpus: int,
        p_size: int,
        p_chunks: int,
        p_times: int,
        diff_sources: bool,
        verbose: bool,
        run: bool):

    # check and read input table
    i_table, tab = check_input_table(i_table, verbose, p_method)

    # read metadata and collect sink / sources
    metadata, column_name, sources, sink = get_metadata(
        m_metadata, p_column_name, p_sources, p_sink, verbose, meth)

    # filter for command line params
    tab, o_dir_path = get_filtered(
        p_column, p_column_value, p_filter_prevalence, p_filter_abundance,
        p_filter_order, p_column_quant, tab, metadata, o_dir_path)

    # filter for min rarefaction depth
    tab, raref = get_rarefaction(tab, p_rarefaction)

    # subset metadata to filtered samples
    metadata = metadata.set_index('sample_name').loc[tab.columns.tolist(), [column_name]]

    # get list of samples per sink / sources
    samples, counts, sources = get_sourcesink_dict(metadata, column_name, sink, sources)
    if len(counts) == 1:
        print('Not enough source(s) samples')
        sys.exit(0)

    # create the output folder
    o_dir_path, o_dir_path_meth = get_o_dir_paths(o_dir_path, column_name, sink,
                                                  sources, p_sources, p_method)

    # write data to be used
    tab_out = write_data_table(tab, samples, o_dir_path, raref)

    if p_method == 'feast':
        cmd = run_feast(
            tab_out,
            o_dir_path_meth,
            samples,
            counts,
            sources,
            sink,
            p_size,
            p_chunks,
            p_iterations_burnins,
            p_rarefaction,
            diff_sources,
            p_times
        )
    elif p_method == 'sourcetracker':
        cmd = run_sourcetracker(
            tab_out,
            o_dir_path_meth,
            samples,
            counts,
            sources,
            sink,
            p_size,
            p_chunks,
            p_iterations_burnins,
            p_rarefaction,
            p_cpus,
            p_times
        )
    elif p_method == 'q2':
        cmd = run_q2classifier(
            tab_out,
            o_dir_path_meth,
            samples,
            counts,
            sources,
            sink,
            p_size,
            p_chunks,
            p_rarefaction,
            p_cpus,
            p_times
        )
    elif p_method == 'metastorms':
        cmd = run_metastorms(
            tab_out,
            o_dir_path_meth,
            samples,
            counts,
            sources,
            sink,
            p_size,
            p_chunks,
            p_iterations_burnins,
            p_rarefaction,
            p_cpus,
            p_times
        )
    elif p_method == 'classify':
        cmd = run_classify(
            tab_out,
            o_dir_path_meth,
            metadata,
            column_name,
            sources,
            sink,
            p_size,
            p_chunks,
            p_iterations_burnins,
            p_rarefaction,
            p_cpus,
            p_times
        )

    script = '%s/cmd_%s.sh' % (o_dir_path_meth, p_method)
    sh = open(script, 'w')
    sh.write('%s\n' % cmd)
    sh.close()
    if run:
        subprocess.call(['sh', script])
