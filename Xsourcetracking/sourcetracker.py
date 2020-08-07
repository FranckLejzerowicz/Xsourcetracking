# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import subprocess
from os.path import isdir, isfile, splitext

from Xsourcetracking.sourcesink import get_chunk_nsources, get_timechunk_meta, get_sink_samples_chunks


def run_sourcetracker(
        tab_out: str,
        o_dir_path_meth: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        p_size: int,
        p_chunks: int,
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_cpus: int,
        p_times: int) -> str:

    # get the sink samples broken down into sublists based on p_sink
    # (all sink samples must be vs. sources but not necessarily at once)
    sink_samples_chunks = get_sink_samples_chunks(samples, sink, p_size, p_chunks)

    biom = '%s.biom' % splitext(tab_out)[0]
    qza = '%s.qza' % splitext(tab_out)[0]
    cmd = 'conda activate st2\n'
    if not isfile(qza):
        cmd += 'biom convert -i %s -o %s --to-hdf5 --table-type="OTU table"\n' % (tab_out, biom)
        cmd += 'qiime tools import --input-path %s --output-path %s --type FeatureTable[Frequency]\n' % (biom, qza)
    for t in range(p_times):
        for cdx, chunk in enumerate(sink_samples_chunks):
            n_sources = get_chunk_nsources(chunk, sources, counts)
            r_meta = get_timechunk_meta(chunk, sink, sources, samples, n_sources, 'sourcetracker')

            map_out = '%s/map.t%s.c%s.tsv' % (o_dir_path_meth, t, cdx)
            print("map_out")
            print(map_out)
            r_meta['#SampleID'] = 's' + r_meta['#SampleID']
            r_meta.to_csv(map_out, index=False, sep='\t')

            cur = '%s/tab.t%s.c%s' % (o_dir_path_meth, t, cdx)
            cur_qza = '%s.qza' % cur
            cur_biom = '%s.biom' % cur

            cur_p_cpus = p_cpus
            if p_cpus > len(chunk):
                cur_p_cpus = len(chunk)

            cmd += 'qiime feature-table filter-samples'
            cmd += ' --i-table %s' % qza
            cmd += ' --m-metadata-file %s' % map_out
            cmd += ' --o-filtered-table %s\n' % cur_qza

            cmd += 'qiime tools export'
            cmd += ' --input-path %s' % cur_qza
            cmd += ' --output-path %s\n' % cur

            cmd += 'mv %s/* %s\n' % (cur, cur_biom)

            o_dir_path_meth_loo = o_dir_path_meth + '/loo_c%s' % cdx
            if isdir(o_dir_path_meth_loo):
                subprocess.call(['rm', '-rf', o_dir_path_meth_loo])

            cmd += 'sourcetracker2'
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

            # cmd += 'rm -rf %s %s %s %s\n' % (cur_qza, cur_biom, map_out, cur)

    return cmd
