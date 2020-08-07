# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from os.path import splitext
from Xsourcetracking.sourcesink import (
    get_chunk_nsources, get_timechunk_meta, get_sink_samples_chunks
)


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

    # get the sink samples broken down into sublists based on p_sink
    # (all sink samples must be vs. sources but not necessarily at once)
    sink_samples_chunks = get_sink_samples_chunks(samples, sink, p_size, p_chunks)

    params = get_params(p_iterations_burnins, p_rarefaction, diff_sources)
    r_script = '%s/run_feast.R' % o_dir_path_meth
    with open(r_script, 'w') as r_o:
        r_o.write('library(FEAST)\n')
        r_o.write('feats_full <- Load_CountMatrix(CountMatrix_path="%s")\n' % tab_out)
        for t in range(p_times):
            for cdx, chunk in enumerate(sink_samples_chunks):
                n_sources = get_chunk_nsources(chunk, sources, counts)
                r_meta = get_timechunk_meta(chunk, sink, sources, samples, n_sources, 'feast')
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
                r_o.write('o.t%s.c%s <- FEAST(C=feat, metadata=meta, dir_path="%s", outfile="o.t%s.c%s"%s)\n' % (
                    t, cdx, o_dir_path_meth, t, cdx, params))
        cmd = 'conda activate feast\nR -f %s --vanilla' % r_script
    return cmd
