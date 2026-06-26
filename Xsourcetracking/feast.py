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
import numpy as np
from os.path import isdir

from Xsourcetracking.utils import (
    get_chunks_set, get_chunks, make_dirs, write_cur_meta)


def get_feast_params(params):
    ps = ''
    if params.get('EM_iterations'):
        ps += ', EM_iterations=%s' % params['EM_iterations']
    if params.get('coverage'):
        ps += ', COVERAGE=%s' % params['coverage']
    if params.get('diff_src'):
        ps += ', different_sources_flag=1'
    else:
        ps += ', different_sources_flag=0'
    return ps


def run_feast(
        i: str,
        o: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        p_chunks: int,
        params: dict
) -> str:

    ps = get_feast_params(params)
    r_script = '%s/run_feast.R' % o
    with open(r_script, 'w') as r_o:
        r_o.write('library(FEAST)\n')
        r_o.write('feats_full <- Load_CountMatrix(CountMatrix_path="%s")\n' % i)
        for t in range(params['times']):
            o_dir = make_dirs(o, t)
            chunks_set = get_chunks_set(samples, sink, p_chunks, params['size'])
            print(p_chunks, params['size'])
            print(len(chunks_set))
            print(chunks_set)
            for r in range(len(chunks_set)):
                chunks = get_chunks(chunks_set, r)
                _, map_pd = write_cur_meta(
                    o_dir, chunks, sources, sink, counts, samples, 'feast', r)
                sams = '","'.join(map_pd['SampleID'].tolist())
                df = 'Env=c("%s"), SourceSink=c("%s"), id=c(%s)' % (
                    '","'.join(map_pd['Env'].tolist()),
                    '","'.join(map_pd['SourceSink'].tolist()),
                    ','.join(map(str, map_pd['id'].tolist())))
                cmd = 'dir_path="%s", outfile="out.r%s"%s' % (o_dir, r, ps)
                r_o.write('samples <- c("%s")\n' % sams)
                r_o.write('meta <- data.frame(%s)\n' % df)
                r_o.write('rownames(meta) <- samples\n')
                r_o.write('feat <- feats_full[samples,]\n')
                r_o.write('feat <- feats_full[,colSums(feats_full)>0]\n')
                r_o.write('FEAST(C=feat, metadata=meta, %s)\n' % cmd)
    cmd = 'R -f %s --vanilla' % r_script
    return cmd
