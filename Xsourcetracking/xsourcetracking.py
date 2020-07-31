# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import sys
import subprocess
import pandas as pd
from os.path import abspath, isfile, isdir

from Xsourcetracking.filter import do_filter
from Xsourcetracking.utils import get_metadata
from Xsourcetracking.run import run_feast, run_sourcetracker, run_classify


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
        diff_sources: bool,
        verbose: bool,
        third_party: bool):

    i_table = abspath(i_table)
    if not isfile(i_table):
        raise IOError("No input table found at %s" % i_table)
    if verbose:
        print('read')
    tab = pd.read_csv(i_table, header=0, index_col=0, sep='\t')

    if verbose:
        print('Read metadata...', end='')
    metadata, column_name, sources, sink = get_metadata(m_metadata, p_column_name, p_sources, p_sink)
    if verbose:
        print('done.')

    o_dir_path = '%s/Snk-%s__Src-%s' % (
        abspath(o_dir_path),
        sink.replace('/', '').replace('(', '').replace(')', '').replace(' ', ''),
        '-'.join([source.replace('/', '').replace('(', '').replace(')', '').replace(' ', '') for source in sources])
    )

    message = 'input'
    if p_column:
        if p_column_value or p_filter_prevalence or p_filter_abundance or p_column_quant:
            tab = do_filter(tab, metadata, p_filter_prevalence,
                            p_filter_abundance, p_filter_order,
                            p_column, p_column_value, p_column_quant)
            message = 'filtered'
            o_dir_path = o_dir_path + '/c-%s' % p_column
            if p_filter_prevalence:
                o_dir_path = o_dir_path + '-' + '-'.join(p_column_value)
            if p_filter_prevalence:
                o_dir_path = o_dir_path + '_p-' + str(p_filter_prevalence)
            if p_filter_prevalence:
                o_dir_path = o_dir_path + '_a-' + str(p_filter_abundance)
            if p_filter_prevalence:
                o_dir_path = o_dir_path + '_q-' + str(p_column_quant)
    if tab.shape[0] < 10:
        raise IOError('Too few features in the %s table' % message)

    if not isdir(o_dir_path):
        os.makedirs(o_dir_path)

    raref = ''
    if p_rarefaction:
        raref = '_raref%s' % p_rarefaction
        tab = tab.loc[:, tab.sum() > p_rarefaction]
    else:
        tab = tab.loc[:, tab.sum() > 1000]

    samples = tab.columns.tolist()
    metadata = metadata.set_index('sample_name').loc[samples, [column_name]]

    tab_out = '%s/tab%s.tsv' % (o_dir_path, raref)
    tab = tab.reset_index()
    tab = tab.rename(columns={tab.columns.tolist()[0]: 'featureid'})
    tab.to_csv(tab_out, index=False, sep='\t')

    o_dir_path_meth = o_dir_path + '/' + p_method
    if not isdir(o_dir_path_meth):
        os.makedirs(o_dir_path_meth)

    if p_method == 'feast':
        cmd = run_feast(
            tab_out,
            o_dir_path_meth,
            metadata,
            column_name,
            sources,
            sink,
            p_iterations_burnins,
            p_rarefaction,
            diff_sources
        )

    elif p_method == 'sourcetracker':
        cmd = run_sourcetracker(
            tab_out,
            o_dir_path_meth,
            metadata,
            column_name,
            sources,
            sink,
            p_iterations_burnins,
            p_rarefaction,
            p_cpus,
        )
    elif p_method == 'classify':
        cmd = run_classify(
            tab,
            tab_out,
            o_dir_path_meth,
            metadata,
            column_name,
            sources,
            sink,
            p_iterations_burnins,
            p_rarefaction,
            p_cpus,
        )
    else:
        sys.exit(1)
    if third_party:
        sh = open('%s/cmd.sh' % o_dir_path, 'w')
        sh.write('%s\n' % cmd)
        sh.close()
    else:
        subprocess.call(cmd)
    print(cmd)
