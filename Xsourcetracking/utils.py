# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import sys
import yaml

import pkg_resources

import numpy as np
import pandas as pd
from os.path import abspath, dirname, isdir, isfile
from Xsourcetracking.sourcesink import get_chunk_nsources, get_timechunk_meta

RESOURCES = pkg_resources.resource_filename("Xsourcetracking", "resources")


def check_folder(out, tool, cmd) -> bool:
    if tool == 'sourcetracker':
        fp = '%s/mixing_proportions.tsv' % out
    elif tool == 'q2_classifier':
        fp = '%s/predictions.tsv' % out
    if isfile(fp):
        return True
    cmd += 'rm -rf %s\n' % out
    return False


def make_dirs(dir_out, t, r=None):
    o_dir = dir_out + '/t%s' % t
    if r:
        o_dir += '/r%s' % r
    if not isdir(o_dir):
        os.makedirs(o_dir)
    return o_dir


def get_cpus(cur_list, p_cpus):
    cpus = p_cpus
    if p_cpus > len(cur_list):
        cpus = len(cur_list)
    return cpus


def write_cur_meta(o_dir, chunks, sources, sink, counts, samples, tool, r=None):
    if tool == 'q2_classifier':
        chunk = chunks
    else:
        chunk = chunks[0]
    n = get_chunk_nsources(chunk, sources, counts)
    map_pd = get_timechunk_meta(chunk, sink, sources, samples, n, tool)
    if tool == 'q2_classifier':
        map_out = '%s/map.model.tsv' % o_dir
    else:
        if tool == 'sourcetracker':
            values = [[sam, 'source', sink] for sam in chunks[1]]
            columns = ['#SampleID', 'SourceSink', 'Env']
        elif tool == 'feast':
            values = [[sam, sink, 'Source', 'NA'] for sam in chunks[1]]
            columns = ['SampleID', 'Env', 'SourceSink', 'id']
        map_pd = pd.concat([map_pd, pd.DataFrame(values, columns=columns)])
        map_out = '%s/map.r%s.tsv' % (o_dir, r)
    map_pd.to_csv(map_out, index=False, sep='\t')
    return map_out, map_pd



def get_chunks(chunks_set, r, rev=False):
    if rev:
        chunk_rs = chunks_set[(r + 1):] + chunks_set[:(r + 1)]
        chunks = [[c for cs in chunk_rs[1:] for c in cs], chunk_rs[0]]
    else:
        chunk_rs = chunks_set[(r + 1):] + chunks_set[:(r + 1)]
        chunks = [chunk_rs[0], [c for cs in chunk_rs[1:] for c in cs]]
    return chunks


def get_chunks_set(samples, sink, p_chunks, p_size) -> list:
    nsink = len(samples[sink])
    if p_chunks:
        if nsink / p_chunks < 100:
            N = 2
        else:
            N = p_chunks
    elif p_size:
        if 0 < p_size < 1:
            n = nsink * p_size
        else:
            n = p_size
        if n < 100:
            N = 2
        else:
            N = nsink / n
    else:
        for r in range(2, 9):
            if nsink / r < 100:
                N = r
                break
        else:
            N = 2
    lspace = np.linspace(0, nsink, num=int(N), endpoint=False)
    idx = np.digitize(range(nsink), bins=lspace)
    chunks = [
        [s for sdx, s in enumerate(samples[sink]) if idx[sdx] == i]
        for i in range(1, int(N) + 1)
    ]
    return chunks


def write_data_table(tab, dir_out, samples, raref, meth):
    tab_out = '%s/tab%s.tsv' % (dirname(dir_out), raref)
    all_samples = set([s for sam in samples.values() for s in sam])
    if not isfile(tab_out):
        print('Writting input data table...', end=' ')
        tab = tab[list(all_samples)]
        tab_reset = tab.reset_index()
        tab_reset = tab_reset.rename(columns={tab_reset.columns.tolist()[0]: 'featureid'})
        tab_reset.to_csv(tab_out, index=False, sep='\t')
        print('done.')
    return tab_out


def get_rarefaction(tab, params):
    raref = ''
    raref_value = 0
    if params['sink_rarefaction_depth'] and params['source_rarefaction_depth']:
        raref_value = min(params['sink_rarefaction_depth'],
                          params['source_rarefaction_depth'])
    elif params['sink_rarefaction_depth']:
        raref_value = params['sink_rarefaction_depth']
    elif params['source_rarefaction_depth']:
        raref_value = params['source_rarefaction_depth']
    if raref_value:
        print('Rarefying...', end=' ')
        raref = '_raref%s' % raref_value
        tab = tab.loc[:, tab.sum() > raref_value]
        print('done.')
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


def get_dir_out(
        o_dir,
        column_name,
        sink,
        sources,
        p_sources,
        p_method
) -> str:
    print('Getting output paths...', end=' ')
    dir_out = '%s/%s-%s' % (
        abspath(o_dir),
        column_name,
        sink.replace(
            '/', '').replace(
            '(', '').replace(
            ')', '').replace(
            ' ', '')
    )
    if p_sources:
        dir_out = '%s_%s' % (
            dir_out,
            '_'.join([source.replace(
                '/', '').replace(
                '(', '').replace(
                ')', '').replace(
                ' ', '') for source in sources])
        )
    dir_out = dir_out + '/' + p_method
    if not isdir(dir_out):
        os.makedirs(dir_out)
    print('done: %s' % dir_out)
    return dir_out


def check_input_table(i_table: str, verbose: bool) -> (str, pd.DataFrame):
    print('Checking input table...', end=' ')
    i_table = abspath(i_table)
    if not isfile(i_table):
        raise IOError("No input table found at %s" % i_table)
    if verbose:
        print('done')
    tab = pd.read_csv(i_table, header=0, index_col=0, sep='\t')
    return i_table, tab


def get_params(yaml_fp):
    params = {}
    if not yaml_fp or not isfile(yaml_fp):
        yaml_fp = '%s/defaults.yml' % RESOURCES
        print( 'No valid config provided. Using: %s' % yaml_fp)
    with open(yaml_fp) as yaml_handle:
        try:
            params = yaml.load(yaml_handle, Loader=yaml.FullLoader)
        except AttributeError:
            params = yaml.load(yaml_handle)
    return params


def get_metadata(m_metadata: str, p_column_name: str,
                 p_sources: tuple, p_sink: str,
                 verbose: bool, meth: str) -> (pd.DataFrame, str, list, str):
    if verbose:
        print('Read metadata...', end=' ')
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
