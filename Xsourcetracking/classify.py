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


def run_classify(
        tab_out: str,
        o_dir_path_meth: str,
        meta: pd.DataFrame,
        column: str,
        sources: tuple,
        sink: str,
        p_size,
        p_chunks,
        p_iterations_burnins: int,
        p_rarefaction: int,
        p_cpus: int,
        p_times: int) -> str:


    # stratifier = meta[column].values
    # if p_size:
    #     if 0 < p_size < 1:
    #         X_train, X_test, y_train, y_test = train_test_split(, y, test_size=0.33, random_state=42)
    #         sink_size = counts[sourcesink] * float(p_size)
    #     elif p_size <= counts[sourcesink]:
    #         sink_size = p_size
    #
    # counts_ = meta[column].value_counts().to_dict()
    # counts = {sink: get_sample_size(counts_, p_size, sink)}
    # for source in sources:
    #     counts.update({source: get_sample_size(counts_, p_size, source)})
    #
    # if p_size:
    #     if 0 < p_size < 1:
    #         sink_size = counts[sourcesink] * float(p_size)
    #     elif p_size <= counts[sourcesink]:
    #         sink_size = p_size
    # if p_size:
    #
    # tab_rad = splitext(tab_out)[0]
    #


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


