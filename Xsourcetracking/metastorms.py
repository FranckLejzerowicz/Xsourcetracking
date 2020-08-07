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

from Xsourcetracking.sourcesink import get_chunk_nsources
from sklearn.model_selection import train_test_split


def run_metastorms(
        tab_out: str,
        o_dir_path_meth: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        p_size,
        p_chunks,
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_cpus: int,
        p_times: int) -> str:

    print(tafdb)
    # for each trial [N]
    for cdx, chunk in enumerate(sink_samples_chunks):
        # get a random reference set of stool samples
        print(tab.T)
        train_test_split()
        # Build a MSE database
            # get from the rest of stool samples, those that are detected as outliers
                # classify the outliers as other sample type

    # cmd = ''
    #     n_sources = get_chunk_nsources(chunk, sources, counts)
    #     for source in sources:
    #         n_source = n_sources[source]
    #         for sodx, sam in enumerate(random.sample(samples[source], n_source)):
    #             map_list.append([sam, 'source', '%s %s' % (source, (sodx + 1))])
    #             cur_sams.append(sam)
    #     map_pd = pd.DataFrame(map_list, columns=['#SampleID', 'SourceSink', 'Env'])
    #     map_out = '%s/map.c%s.tsv' % (o_dir_path_meth, cdx)
    #     map_pd.to_csv(map_out, index=False, sep='\t')
    #
    #     cur_tab = tab.loc[:, cur_sams].copy()
    #     cur_tab = cur_tab.loc[cur_tab.sum(1) > 0, ]
    #     cur_tab_out = '%s/tab.c%s.tsv' % (o_dir_path_meth, cdx)
    #     cur_tab.reset_index().to_csv(cur_tab_out, index=False, sep='\t')
    #
    #     o_dir_path_meth_prop = o_dir_path_meth + '/prop_c%s' % cdx
    #     if isdir(o_dir_path_meth_prop):
    #         subprocess.call(['rm', '-rf', o_dir_path_meth_prop])
    #     o_dir_path_meth_loo = o_dir_path_meth + '/loo_c%s' % cdx
    #     if isdir(o_dir_path_meth_loo):
    #         subprocess.call(['rm', '-rf', o_dir_path_meth_loo])
    #
    #     cmd += 'sourcetracker2 gibbs \\\n'
    #     cmd += ' -i %s \\\n' % cur_tab_biom
    #     cmd += ' -m %s \\\n' % map_out
    #     if p_rarefaction:
    #         cmd += ' --source_rarefaction_depth %s \\\n' % p_rarefaction
    #         cmd += ' --sink_rarefaction_depth %s \\\n' % p_rarefaction
    #     if p_iterations_burnins:
    #         cmd += ' --burnin %s \\\n' % p_iterations_burnins
    #     cmd += ' --loo \n\n'
    #     cmd += ' --jobs %s \\\n' % cur_p_cpus
    #     cmd += ' -o %s/\n\n' % o_dir_path_meth_loo
    # return cmd
