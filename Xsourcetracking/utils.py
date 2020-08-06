# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import pandas as pd
from os.path import abspath, isdir, isfile


def write_data_table(tab, samples, o_dir_path, raref):
    tab_out = '%s/tab%s.tsv' % (o_dir_path, raref)
    all_samples = set([s for sam in samples.values() for s in sam])
    if not isfile(tab_out):
        tab = tab[list(all_samples)]
        tab_reset = tab.reset_index()
        tab_reset = tab_reset.rename(columns={tab_reset.columns.tolist()[0]: 'featureid'})
        tab_reset.to_csv(tab_out, index=False, sep='\t')
    return tab_out


def get_rarefaction(tab, p_rarefaction):
    raref = ''
    if p_rarefaction:
        raref = '_raref%s' % p_rarefaction
        tab = tab.loc[:, tab.sum() > p_rarefaction]
    else:
        tab = tab.loc[:, tab.sum() > 1000]
    return tab, raref


def get_o_dir_path(o_dir_path, counts, sink, sources, p_method) -> (str, str):
    o_dir_path = '%s/Snk-%s%s__Src-%s' % (
        abspath(o_dir_path),
        counts[sink],
        sink.replace('/', '').replace(
            '(', '').replace(')', '').replace(
            ' ', ''),
        '-'.join(['%s%s' % (counts[source], source.replace(
            '/', '').replace(
            '(', '').replace(
            ')', '').replace(
            ' ', '')) for source in sources])
    )
    o_dir_path_meth = o_dir_path + '/' + p_method
    if not isdir(o_dir_path_meth):
        os.makedirs(o_dir_path_meth)
    return o_dir_path, o_dir_path_meth


def check_input_table(i_table: str, verbose: bool) -> (str, pd.DataFrame):
    i_table = abspath(i_table)
    if not isfile(i_table):
        raise IOError("No input table found at %s" % i_table)
    if verbose:
        print('read')
    tab = pd.read_csv(i_table, header=0, index_col=0, sep='\t')
    return i_table, tab


def get_metadata(m_metadata: str, p_column_name: str,
                 p_sources: tuple, p_sink: str,
                 verbose: bool) -> (pd.DataFrame, str, list, str):
    if verbose:
        print('Read metadata...', end='')
    with open(m_metadata) as f:
        for line in f:
            break
    metadata = pd.read_csv(m_metadata, header=0, sep='\t', dtype={line.split('\t')[0]: str})
    metadata = metadata.rename(columns={metadata.columns.tolist()[0]: 'sample_name'})
    metadata.columns = [x.replace('\n', '') for x in metadata.columns]
    if p_column_name not in metadata.columns.tolist()[1:]:
        raise IOError('"%s" not in "%s"' % (p_column_name, m_metadata))
    metadata_factors = metadata[p_column_name].unique().tolist()
    if p_sink not in metadata_factors:
        raise IOError('Sink "%s" not in "%s" column "%s"' % (p_sink, m_metadata, p_column_name))
    if p_sources:
        sources = []
        for p_source in p_sources:
            if p_source not in metadata_factors:
                raise IOError('Source "%s" not in "%s" column "%s"' % (p_source, m_metadata, p_column_name))
            sources.append(p_source)
    else:
        sources = [x for x in metadata_factors if str(x) not in ['nan', p_sink]]
    if verbose:
        print('done.')
    return metadata, p_column_name, sources, p_sink
