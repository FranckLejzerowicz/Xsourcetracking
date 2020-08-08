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
from os.path import isdir

from Xsourcetracking.utils import get_chunks
from Xsourcetracking.sourcesink import get_chunk_nsources, get_timechunk_meta


def get_params(p_iterations_burnins, p_rarefaction, diff_sources):
    params = ''
    if p_iterations_burnins:
        params += ', EM_iterations=%s' % p_iterations_burnins
    if p_rarefaction:
        params += ', COVERAGE=%s' % p_rarefaction
    if diff_sources:
        params += ', different_sources_flag=1'
    else:
        params += ', different_sources_flag=0'
    return params


def run_feast(
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
        diff_sources: bool,
        p_times: int) -> str:

    params = get_params(p_iterations_burnins, p_rarefaction, diff_sources)
    r_script = '%s/run_feast.R' % o_dir_path_meth
    with open(r_script, 'w') as r_o:
        r_o.write('library(FEAST)\n')
        r_o.write('feats_full <- Load_CountMatrix(CountMatrix_path="%s")\n' % tab_out)
        for t in range(p_times):

            o_dir_path_meth_t = o_dir_path_meth + '/t%s' % t
            if isdir(o_dir_path_meth_t):
                subprocess.call(['rm', '-rf', o_dir_path_meth_t])
            os.makedirs(o_dir_path_meth_t)

            chunks_set = get_chunks(samples, sink, p_chunks, p_size)
            for r in range(len(chunks_set)):

                chunks = chunks_set[(r + 1):] + chunks_set[:(r + 1)]
                chunks = [chunks[0], [c for chunk in chunks[1:] for c in chunk]]

                n_sources = get_chunk_nsources(chunks[0], sources, counts)
                r_meta = get_timechunk_meta(chunks[0], sink, sources, samples, n_sources, 'feast')
                r_meta = pd.concat([
                    r_meta,
                    pd.DataFrame([[sam, sink, 'Source', len(sources)] for sam in chunks[1]],
                                 columns=['SampleID', 'Env', 'SourceSink', 'id'])
                ])
                map_out = '%s/map.r%s.tsv' % (o_dir_path_meth_t, r)
                r_meta.to_csv(map_out, index=False, sep='\t')

                sams = '","'.join(r_meta['SampleID'].tolist())
                r_o.write('samples <- c("%s")\n' % sams)
                r_o.write('meta <- data.frame(Env=c("%s"), SourceSink=c("%s"), id=c(%s))\n' % (
                    '","'.join(r_meta['Env'].tolist()),
                    '","'.join(r_meta['SourceSink'].tolist()),
                    ','.join(map(str, r_meta['id'].tolist())),
                ))
                r_o.write('rownames(meta) <- samples\n')
                r_o.write('feat <- feats_full[samples,]\n' % ())
                r_o.write('feat <- feats_full[,colSums(feats_full)>0]\n' % ())
                r_o.write('FEAST(C=feat, metadata=meta, dir_path="%s", outfile="out.r%s"%s)\n' % (
                    o_dir_path_meth_t, r, params))

    cmd = 'conda activate feast\nR -f %s --vanilla' % r_script
    return cmd
