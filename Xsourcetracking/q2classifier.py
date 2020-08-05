# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import random
import subprocess
import pandas as pd
from os.path import isdir, splitext

from Xsourcetracking.sourcesink import get_chunk_nsources


def run_q2classifier(
        tab: pd.DataFrame,
        o_dir_path_meth: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        sink_samples_chunks: list,
        p_rarefaction: int,
        p_cpus: int):

    cmd = ''
    for cdx, chunk in enumerate(sink_samples_chunks):
        map_list = []
        cur_sams = []
        for sidx, sam in enumerate(chunk):
            map_list.append([sam, sink])
            cur_sams.append(sam)
        cur_p_cpus = p_cpus
        if p_cpus > sidx:
            cur_p_cpus = sidx
        n_sources = get_chunk_nsources(chunk, sources, counts)
        for source in sources:
            n_source = n_sources[source]
            for sodx, sam in enumerate(random.sample(samples[source], n_source)):
                map_list.append([sam, source])
                cur_sams.append(sam)
        map_pd = pd.DataFrame(map_list, columns=['#SampleID', 'Env'])
        map_out = '%s/map.c%s.tsv' % (o_dir_path_meth, cdx)
        map_pd.to_csv(map_out, index=False, sep='\t')
        cur_tab = tab.loc[:, cur_sams].copy()
        cur_tab = cur_tab.loc[cur_tab.sum(1) > 0, ]
        tsv = '%s/tab.c%s.tsv' % (o_dir_path_meth, cdx)
        cur_tab.reset_index().to_csv(tsv, index=False, sep='\t')

        rad = splitext(tsv)[0]
        biom = '%s.biom' % rad
        qza_ = '%s.qza' % rad
        cmd += 'biom convert -i %s -o %s --to-hdf5 --table-type="OTU table"\n' % (tsv, biom)
        cmd += 'qiime tools import --input-path %s --output-path %s --type FeatureTable[Frequency]\n' % (biom, qza_)
        if p_rarefaction:
            cmd += 'qiime feature-table rarefy --i-table %s \\\n' % qza_
            cmd += '--p-sampling-depth 1000 \\\n'
            cmd += '--o-rarefied-table %s_raref1000.qza\n' % rad
            qza = '%s_raref1000.qza' % rad
        else:
            qza = qza_

        for estimator in ['RandomForestClassifier',
                          'GradientBoostingClassifier',
                          'AdaBoostClassifier',
                          'LinearSVC']:
            o_dir_path_meth_est = o_dir_path_meth + '/%s/c%s' % (estimator, cdx)
            if isdir(o_dir_path_meth_est):
                subprocess.call(['rm', '-rf', o_dir_path_meth_est])
            os.makedirs(o_dir_path_meth_est)

            cmd += 'qiime sample-classifier classify-samples \\\n'
            cmd += ' --i-table %s \\\n' % qza
            cmd += ' --m-metadata-file %s \\\n' % map_out
            cmd += ' --m-metadata-column Env \\\n'
            cmd += ' --p-cv 1 \\\n'
            cmd += ' --p-n-jobs %s \\\n' % cur_p_cpus
            cmd += ' --p-estimator %s \\\n' % estimator
            sample_estimator = '%s/sample_estimator.qza' % o_dir_path_meth_est
            cmd += ' --o-sample-estimator %s \\\n' % sample_estimator
            feature_importance = '%s/feature_importance.qza' % o_dir_path_meth_est
            cmd += ' --o-feature-importance %s \\\n' % feature_importance
            predictions = '%s/predictions.qza' % o_dir_path_meth_est
            cmd += ' --o-predictions %s \\\n' % predictions
            model_summary = '%s/model_summary.qza' % o_dir_path_meth_est
            cmd += ' --o-model-summary %s \\\n' % model_summary
            accuracy_results = '%s/accuracy_results.qzv' % o_dir_path_meth_est
            cmd += ' --o-accuracy-results %s \\\n' % accuracy_results
            probabilities = '%s/probabilities.qza' % o_dir_path_meth_est
            cmd += ' --o-probabilities %s \\\n' % probabilities
            heatmap = '%s/heatmap.qzv' % o_dir_path_meth_est
            cmd += ' --o-heatmap %s\n' % heatmap

            feature_importance_d = splitext(feature_importance)[0]
            cmd += 'qiime tools export --input-path %s --output-path %s\n' % (feature_importance, feature_importance_d)
            cmd += 'mv  %s/* %s.tsv\n' % (feature_importance_d, feature_importance_d)
            predictions_d = splitext(predictions)[0]
            cmd += 'qiime tools export --input-path %s --output-path %s\n' % (predictions, predictions_d)
            cmd += 'mv  %s/* %s.tsv\n' % (predictions_d, predictions_d)
            probabilities_d = splitext(probabilities)[0]
            cmd += 'qiime tools export --input-path %s --output-path %s\n' % (probabilities, probabilities_d)
            cmd += 'mv  %s/* %s.tsv\n' % (probabilities_d, probabilities_d)
            cmd += 'rm -rf %s %s %s %s %s %s %s %s %s\n\n\n' % (biom, qza, sample_estimator, feature_importance,
                                                       predictions, probabilities, feature_importance_d, predictions_d,
                                                       probabilities_d)

    return cmd
