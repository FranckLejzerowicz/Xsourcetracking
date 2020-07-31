# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import random
import subprocess
import pandas as pd
from os.path import isdir, splitext

from sklearn.model_selection import train_test_split


def run_feast(
        tab_out: str,
        o_dir_path_meth: str,
        meta: pd.DataFrame,
        column: str,
        sources: tuple,
        sink: str,
        p_iterations_burnins: int,
        p_rarefaction: int,
        diff_sources: bool) -> str:

    counts = meta[column].value_counts().to_dict()
    tab_rad = splitext(tab_out)[0]

    params = ''
    if p_iterations_burnins:
        params += ', EM_iterations=%s' % p_iterations_burnins
    if p_rarefaction:
        params += ', COVERAGE=%s' % p_rarefaction
    if diff_sources:
        params += ', different_sources_flag=1'
    else:
        params += ', different_sources_flag=0'

    r_script = '%s_FEAST.R' % tab_rad
    with open(r_script, 'w') as r_o:
        r_o.write('library(FEAST)\n')
        r_o.write('feats_full <- Load_CountMatrix(CountMatrix_path="%s")\n' % tab_out)
        for r in range(2):

            r_meta_list = []
            for sdx, sam in enumerate(random.sample(meta.loc[meta[column] == sink, :].index.tolist(), int(counts[sink] * 0.5))):
                r_meta_list.append([sam, '%s %s' % (sink, (sdx + 1)), 'Sink', (sdx + 1)])
            for sodx, source in enumerate(sources):
                for sadx, sam in enumerate(random.sample(meta.loc[meta[column] == source, :].index.tolist(), int(counts[source] * 0.5))):
                    r_meta_list.append([sam, '%s %s' % (source, (sadx + 1)), 'Source', sodx])
            r_meta = pd.DataFrame(r_meta_list, columns=['SampleID', 'Env', 'SourceSink', 'id'])

            samples = '","'.join(r_meta['SampleID'].tolist())
            r_o.write('samples <- c("%s")\n' % samples)
            r_o.write('meta <- data.frame(Env=c("%s"), SourceSink=c("%s"), id=c(%s))\n' % (
                '","'.join(r_meta['Env'].tolist()),
                '","'.join(r_meta['SourceSink'].tolist()),
                ','.join(map(str, r_meta['id'].tolist())),
            ))
            r_o.write('rownames(meta) <- samples\n')
            r_o.write('feat <- feats_full[samples,]\n' % ())
            r_o.write('o.%s <- FEAST(C=feat, metadata=meta, dir_path="%s_feast", outfile="o.%s"%s)\n' % (
                r, o_dir_path_meth, r, params))
    cmd = 'R -f %s --vanilla' % r_script
    return cmd


def run_sourcetracker(
        tab_out: str,
        o_dir_path_meth: str,
        meta: pd.DataFrame,
        column: str,
        sources: tuple,
        sink: str,
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_cpus: int):

    map_list = []
    for sidx, sam in enumerate(meta.loc[meta[column] == sink, :].index.tolist()):
        map_list.append([sam, 'sink', '%s %s' % (sink, (sidx + 1))])
    if p_cpus > sidx:
        p_cpus = sidx
    for source in sources:
        for sodx, sam in enumerate(meta.loc[meta[column] == source, :].index.tolist()):
            map_list.append([sam, 'source', '%s %s' % (source, (sodx + 1))])
    map_pd = pd.DataFrame(map_list, columns=['#SampleID', 'SourceSink', 'Env'])
    map_out = '%s/map.tsv' % o_dir_path_meth
    map_pd.to_csv(map_out, index=False, sep='\t')

    o_dir_path_meth_prop = o_dir_path_meth + '/prop'
    if isdir(o_dir_path_meth_prop):
        subprocess.call(['rm', '-rf', o_dir_path_meth_prop])
    o_dir_path_meth_loo = o_dir_path_meth + '/loo'
    if isdir(o_dir_path_meth_loo):
        subprocess.call(['rm', '-rf', o_dir_path_meth_loo])

    tab_rad = splitext(tab_out)[0]
    tab_biom = '%s.biom' % tab_rad
    cmd = 'biom convert -i %s -o %s --to-hdf5 --table-type="OTU table"\n' % (tab_out, tab_biom)
    cmd += 'sourcetracker2 gibbs \\\n'
    cmd += ' -i %s \\\n' % tab_biom
    cmd += ' -m %s \\\n' % map_out
    if p_rarefaction:
        cmd += ' --source_rarefaction_depth %s \\\n' % p_rarefaction
        cmd += ' --sink_rarefaction_depth %s \\\n' % p_rarefaction
    if p_iterations_burnins:
        cmd += ' --burnin %s \\\n' % p_iterations_burnins
    cmd += ' --jobs %s \\\n' % p_cpus
    cmd += ' -o %s/\n' % o_dir_path_meth_prop

    cmd += 'sourcetracker2 gibbs \\\n'
    cmd += ' -i %s \\\n' % tab_biom
    cmd += ' -m %s \\\n' % map_out
    if p_rarefaction:
        cmd += ' --source_rarefaction_depth %s \\\n' % p_rarefaction
        cmd += ' --sink_rarefaction_depth %s \\\n' % p_rarefaction
    if p_iterations_burnins:
        cmd += ' --burnin %s \\\n' % p_iterations_burnins
    cmd += ' --jobs %s \\\n' % p_cpus
    cmd += ' -o %s/\n' % o_dir_path_meth_loo
    return cmd


def run_classify(
        tab: pd.DataFrame,
        tab_out: str,
        o_dir_path_meth: str,
        meta: pd.DataFrame,
        column: str,
        sources: tuple,
        sink: str,
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_cpus: int):

    # params = ''
    # if p_iterations_burnins:
    #     params += ', EM_iterations=%s' % p_iterations_burnins
    # if p_rarefaction:
    #     params += ', COVERAGE=%s' % p_rarefaction
    # if diff_sources:
    #     params += ', different_sources_flag=1'
    # else:
    #     params += ', different_sources_flag=0'

    counts = meta[column].value_counts().to_dict()
    tab_rad = splitext(tab_out)[0]

    meta_list = []
    sink_sams = meta.loc[meta[column] == sink, :].index.tolist()
    tab = tab.T
    print(tab.iloc[:4, :4])
    print(tab.shape)
    print(len(sink_sams))
    print(tfds)
    # tab_sink = tab.loc[sink_sams]

    # train_test_split(, test_size=0.3, random_state=0)

    sources_sams = dict((source, meta.loc[meta[column] == source, :].index.tolist()) for source in sources)

    for r in range(2):
        pass


