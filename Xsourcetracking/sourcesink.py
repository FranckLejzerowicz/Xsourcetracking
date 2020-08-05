# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import random
import pandas as pd


def get_chunk_nsources(chunk, sources, counts):
    len_chunk = len(chunk)
    n_sources = {}
    for source in sources:
        n_source = counts[source]
        if n_source >= len_chunk:
            n_sources[source] = len_chunk
        else:
            n_sources[source] = n_source
    return n_sources


def get_timechunk_meta(chunk, sink, sources, samples, n_sources):
    r_meta_list = []
    for sdx, sam in enumerate(chunk):
        r_meta_list.append([sam, '%s %s' % (sink, (sdx + 1)), 'Sink', (sdx + 1)])
    for sodx, source in enumerate(sources):
        for sadx, sam in enumerate(random.sample(samples[source], n_sources[source])):
            r_meta_list.append([sam, '%s %s' % (source, (sadx + 1)), 'Source', sodx])
    r_meta = pd.DataFrame(r_meta_list, columns=['SampleID', 'Env', 'SourceSink', 'id'])
    return r_meta


def get_sink_samples_chunks(samples, sink, p_size, p_chunks):
    if p_chunks:
        print(samples[sink])
        print(p_chunks)
        sink_samples_chunks_final = chunks(samples[sink], p_chunks)
    elif p_size:
        if 0 < p_size < 1:
            n = len(samples[sink]) * p_size
        else:
            n = int(p_size)
        # https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
        sink_samples_chunks = [samples[sink][i*n:(i+1)*n] for i in range((len(samples[sink])+n-1)//n)]
        sink_samples_chunks_final = sink_samples_chunks[:-1]
        sink_samples_chunks_final[-1].extend(sink_samples_chunks[-1])
    else:
        sink_samples_chunks_final = [samples[sink]]
    return sink_samples_chunks_final


def get_sourcesink_dict(metadata, column_name, sink, sources):
    counts = metadata[column_name].value_counts().to_dict()
    samples = {sink: metadata.loc[metadata[column_name] == sink, :].index.tolist()}
    for source in sources:
        if counts[source] < 20:
            del counts[source]
            continue
        samples.update({source: metadata.loc[metadata[column_name] == source, :].index.tolist()})
    sources = [x for x in sources if x in counts]
    return samples, counts, sources
