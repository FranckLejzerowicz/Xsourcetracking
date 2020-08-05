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
from Xsourcetracking.sourcesink import get_chunk_nsources, get_timechunk_meta


def run_sourcetracker(
        tab_out: str,
        o_dir_path_meth: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        sink_samples_chunks: list,
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_cpus: int,
        p_times: int) -> str:

    biom = '%s.biom' % splitext(tab_out)[0]
    qza = '%s.qza' % splitext(tab_out)[0]
    cmd = 'biom convert -i %s -o %s --to-hdf5 --table-type="OTU table"\n' % (tab_out, biom)
    cmd += 'qiime tools import --input-path %s --output-path %s --type FeatureTable[Frequency]\n' % (biom, qza)
    for t in range(p_times):
        for cdx, chunk in enumerate(sink_samples_chunks):
            n_sources = get_chunk_nsources(chunk, sources, counts)
            r_meta = get_timechunk_meta(chunk, sink, sources, samples, n_sources, 'feast')

            # for sidx, sam in enumerate(chunk):
            #     map_list.append([sam, 'sink', '%s %s' % (sink, (sidx + 1))])
            #     cur_sams.append(sam)
            # for source in sources:
            #     n_source = n_sources[source]
            #     for sodx, sam in enumerate(random.sample(samples[source], n_source)):
            #         map_list.append([sam, 'source', '%s %s' % (source, (sodx + 1))])
            #         cur_sams.append(sam)
            # map_pd = pd.DataFrame(map_list, columns=['#SampleID', 'SourceSink', 'Env'])

            map_out = '%s/map.t%s.c%s.tsv' % (o_dir_path_meth, t, cdx)
            r_meta.to_csv(map_out, index=False, sep='\t')

            cur_qza = '%s/tab.t%s.c%s.qza' % (o_dir_path_meth, t, cdx)
            cur_biom = '%s/tab.t%s.c%s.biom' % (o_dir_path_meth, t, cdx)
            # cur_tab = tab.loc[:, r_meta['#SampleID']].copy()
            # cur_tab = cur_tab.loc[cur_tab.sum(1) > 0, ]
            # cur_tab.reset_index().to_csv(cur_tab_out, index=False, sep='\t')

            cur_p_cpus = p_cpus
            if p_cpus > len(chunk):
                cur_p_cpus = len(chunk)

            cmd += 'qiime feature-table filter-samples'
            cmd += ' --i-table %s' % qza
            cmd += ' --m-metadata-file %s' % map_out
            cmd += ' --o-filtered-table %s\n' % cur_qza

            cmd += 'qiime tools export'
            cmd += ' --input-path %s' % cur_qza
            cmd += ' --output-path %s' % cur_biom
            cmd += ' --to-tsv\n'

            # o_dir_path_meth_prop = o_dir_path_meth + '/prop_c%s' % cdx
            # if isdir(o_dir_path_meth_prop):
            #     subprocess.call(['rm', '-rf', o_dir_path_meth_prop])
            # cmd += 'sourcetracker2 gibbs'
            # cmd += ' -i %s' % cur_biom
            # cmd += ' -m %s' % map_out
            # if p_rarefaction:
            #     cmd += ' --source_rarefaction_depth %s' % p_rarefaction
            #     cmd += ' --sink_rarefaction_depth %s' % p_rarefaction
            # if p_iterations_burnins:
            #     cmd += ' --burnin %s' % p_iterations_burnins
            # cmd += ' --jobs %s' % cur_p_cpus
            # cmd += ' -o %s/\n\n' % o_dir_path_meth_prop

            o_dir_path_meth_loo = o_dir_path_meth + '/loo_c%s' % cdx
            if isdir(o_dir_path_meth_loo):
                subprocess.call(['rm', '-rf', o_dir_path_meth_loo])
            cmd += 'sourcetracker2 gibbs'
            cmd += ' -i %s' % cur_biom
            cmd += ' -m %s' % map_out
            if p_rarefaction:
                cmd += ' --source_rarefaction_depth %s' % p_rarefaction
                cmd += ' --sink_rarefaction_depth %s' % p_rarefaction
            if p_iterations_burnins:
                cmd += ' --burnin %s' % p_iterations_burnins
            cmd += ' --loo'
            cmd += ' --jobs %s' % cur_p_cpus
            cmd += ' -o %s/\n' % o_dir_path_meth_loo

            cmd += 'rm -o %s %s %s\n' % (cur_qza, cur_biom, map_out)

    return cmd
