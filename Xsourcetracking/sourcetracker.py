# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import subprocess
import pandas as pd
from os.path import isdir, isfile, splitext

from Xsourcetracking.utils import get_chunks
from Xsourcetracking.sourcesink import get_chunk_nsources, get_timechunk_meta


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

    cmd = 'source activate st2\n'
    biom = '%s.biom' % splitext(tab_out)[0]
    if not isfile(biom):
        cmd += 'biom convert -i %s -o %s --to-hdf5 --table-type="OTU table"\n' % (tab_out, biom)
    for t in range(p_times):

        o_dir_path_meth_t = o_dir_path_meth + '/t%s' % t
        if not isdir(o_dir_path_meth_t):
            os.makedirs(o_dir_path_meth_t)

        chunks_set = get_chunks(samples, sink, p_chunks, p_size)
        for r in range(len(chunks_set)):

            chunks = chunks_set[(r+1):] + chunks_set[:(r+1)]
            chunks = [chunks[0], [c for chunk in chunks[1:] for c in chunk]]

            n_sources = get_chunk_nsources(chunks[0], sources, counts)
            r_meta = get_timechunk_meta(chunks[0], sink, sources, samples, n_sources, 'sourcetracker')
            r_meta = pd.concat([
                r_meta,
                pd.DataFrame([[sam, 'source', sink] for sam in chunks[1]],
                             columns=['#SampleID', 'SourceSink', 'Env'])
            ])
            map_out = '%s/map.r%s.tsv' % (o_dir_path_meth_t, r)
            r_meta.to_csv(map_out, index=False, sep='\t')

            cur_p_cpus = p_cpus
            if p_cpus > len(chunks[0]):
                cur_p_cpus = len(chunks[0])

            o_dir_path_meth_t_r = o_dir_path_meth_t + '/r%s' % r
            if isdir(o_dir_path_meth_t_r):
                subprocess.call(['rm', '-rf', o_dir_path_meth_t_r])

            cmd += 'sourcetracker2'
            cmd += ' -i %s' % biom
            cmd += ' -m %s' % map_out
            if p_rarefaction:
                cmd += ' --source_rarefaction_depth %s' % p_rarefaction
                cmd += ' --sink_rarefaction_depth %s' % p_rarefaction
            if p_iterations_burnins:
                cmd += ' --burnin %s' % p_iterations_burnins
            # cmd += ' --loo'
            cmd += ' --jobs %s' % cur_p_cpus
            cmd += ' -o %s\n' % o_dir_path_meth_t_r

            # cmd += 'rm -rf %s\n' % map_out
    return cmd
