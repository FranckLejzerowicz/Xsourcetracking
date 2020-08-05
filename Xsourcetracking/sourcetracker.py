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
from Xsourcetracking.sourcesink import get_chunk_nsources


def get_sample_size(counts_dict: dict, p_size: float,
                    sourcesink: str) -> int:
    if p_size:
        if 0 < p_size < 1:
            sink_size = counts_dict[sourcesink] * p_size
        elif p_size <= counts_dict[sourcesink]:
            sink_size = p_size
        else:
            sink_size = counts_dict[sourcesink] * 0.5
    else:
        sink_size = counts_dict[sourcesink] * 0.5
    return int(sink_size)


def run_sourcetracker(
        tab: pd.DataFrame,
        o_dir_path_meth: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        sink_samples_chunks: list,
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_cpus: int):

    cmd = ''
    for cdx, chunk in enumerate(sink_samples_chunks):
        map_list = []
        cur_sams = []
        for sidx, sam in enumerate(chunk):
            map_list.append([sam, 'sink', '%s %s' % (sink, (sidx + 1))])
            cur_sams.append(sam)
        cur_p_cpus = p_cpus
        if p_cpus > sidx:
            cur_p_cpus = sidx
        n_sources = get_chunk_nsources(chunk, sources, counts)
        for source in sources:
            n_source = n_sources[source]
            for sodx, sam in enumerate(random.sample(samples[source], n_source)):
                map_list.append([sam, 'source', '%s %s' % (source, (sodx + 1))])
                cur_sams.append(sam)
        map_pd = pd.DataFrame(map_list, columns=['#SampleID', 'SourceSink', 'Env'])
        map_out = '%s/map.c%s.tsv' % (o_dir_path_meth, cdx)
        map_pd.to_csv(map_out, index=False, sep='\t')
        cur_tab = tab.loc[:, cur_sams].copy()
        cur_tab = cur_tab.loc[cur_tab.sum(1) > 0, ]
        cur_tab_out = '%s/tab.c%s.tsv' % (o_dir_path_meth, cdx)
        cur_tab.reset_index().to_csv(cur_tab_out, index=False, sep='\t')

        o_dir_path_meth_prop = o_dir_path_meth + '/prop_c%s' % cdx
        if isdir(o_dir_path_meth_prop):
            subprocess.call(['rm', '-rf', o_dir_path_meth_prop])
        o_dir_path_meth_loo = o_dir_path_meth + '/loo_c%s' % cdx
        if isdir(o_dir_path_meth_loo):
            subprocess.call(['rm', '-rf', o_dir_path_meth_loo])

        cur_tab_biom = '%s.biom' % splitext(cur_tab_out)[0]

        cmd += 'biom convert -i %s -o %s --to-hdf5 --table-type="OTU table"\n' % (cur_tab_out, cur_tab_biom)

        # cmd += 'sourcetracker2 gibbs \\\n'
        # cmd += ' -i %s \\\n' % cur_tab_biom
        # cmd += ' -m %s \\\n' % map_out
        # if p_rarefaction:
        #     cmd += ' --source_rarefaction_depth %s \\\n' % p_rarefaction
        #     cmd += ' --sink_rarefaction_depth %s \\\n' % p_rarefaction
        # if p_iterations_burnins:
        #     cmd += ' --burnin %s \\\n' % p_iterations_burnins
        # cmd += ' --jobs %s \\\n' % cur_p_cpus
        # cmd += ' -o %s/\n\n' % o_dir_path_meth_prop

        cmd += 'sourcetracker2 gibbs \\\n'
        cmd += ' -i %s \\\n' % cur_tab_biom
        cmd += ' -m %s \\\n' % map_out
        if p_rarefaction:
            cmd += ' --source_rarefaction_depth %s \\\n' % p_rarefaction
            cmd += ' --sink_rarefaction_depth %s \\\n' % p_rarefaction
        if p_iterations_burnins:
            cmd += ' --burnin %s \\\n' % p_iterations_burnins
        cmd += ' --loo \\\n'
        cmd += ' --jobs %s \\\n' % cur_p_cpus
        cmd += ' -o %s/\n\n' % o_dir_path_meth_loo
    return cmd
