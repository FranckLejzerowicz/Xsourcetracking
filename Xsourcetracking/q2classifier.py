# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import os
import subprocess
from os.path import isdir, isfile, splitext

from Xsourcetracking.utils import get_chunks
from Xsourcetracking.sourcesink import get_chunk_nsources, get_timechunk_meta


def run_q2classifier(
        tab_out: str,
        o_dir_path_meth: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        p_size: int,
        p_chunks: int,
        p_rarefaction: int,
        p_cpus: int,
        p_times: int) -> str:

    res = []

    cmd = ''
    biom = '%s.biom' % splitext(tab_out)[0]
    qza = '%s.qza' % splitext(tab_out)[0]
    if not isfile(qza):
        cmd += 'biom convert -i %s -o %s --to-hdf5 --table-type="OTU table"\n' % (tab_out, biom)
        cmd += 'qiime tools import --input-path %s --output-path %s --type FeatureTable[Frequency]\n' % (biom, qza)

    for t in range(p_times):
        chunks_set = get_chunks(samples, sink, p_chunks, p_size)
        for r in range(len(chunks_set)):
            chunks = chunks_set[(r+1):] + chunks_set[:(r+1)]
            chunks = [chunks[0], [c for chunk in chunks[1:] for c in chunk]]
            for cdx, chunk in enumerate(chunks):

                cur_p_cpus = p_cpus
                if p_cpus > len(chunk):
                    cur_p_cpus = len(chunk)

                if cdx:
                    # to predict
                    cur = '%s/tab.pred' % o_dir_path_meth_tr
                    map_out = '%s/map.pred.tsv' % o_dir_path_meth_tr
                    with open(map_out, 'w') as o:
                        o.write('#SampleID\tEnv\n')
                        for c in chunk:
                            o.write('%s\t%s\n' % (c, sink))
                else:
                    o_dir_path_meth_tr = o_dir_path_meth + '/t%s/r%s' % (t, r)
                    if isdir(o_dir_path_meth_tr):
                        subprocess.call(['rm', '-rf', o_dir_path_meth_tr])
                    os.makedirs(o_dir_path_meth_tr)

                    # model
                    cur = '%s/tab.model' % o_dir_path_meth_tr
                    map_out = '%s/map.model.tsv' % o_dir_path_meth_tr
                    n_sources = get_chunk_nsources(chunk, sources, counts)
                    r_meta = get_timechunk_meta(chunk, sink, sources, samples, n_sources, 'q2')
                    r_meta.to_csv(map_out, index=False, sep='\t')

                cur_qza_ = '%s.qza' % cur
                cmd += 'qiime feature-table filter-samples'
                cmd += ' --i-table %s' % qza
                cmd += ' --m-metadata-file %s' % map_out
                cmd += ' --o-filtered-table %s\n' % cur_qza_

                if p_rarefaction:
                    cmd += 'qiime feature-table rarefy'
                    cmd += ' --i-table %s' % cur_qza_
                    cmd += ' --p-sampling-depth 1000'
                    cmd += ' --o-rarefied-table %s_raref1000.qza\n' % cur
                    cur_qza = '%s_raref1000.qza' % cur
                else:
                    cur_qza = cur_qza_

                for estimator in [
                    'RandomForestClassifier',
                    # 'GradientBoostingClassifier',
                    # 'AdaBoostClassifier',
                    # 'LinearSVC'
                ]:

                    o_dir_path_meth_est = o_dir_path_meth_tr + '/%s' % estimator
                    if isdir(o_dir_path_meth_est):
                        subprocess.call(['rm', '-rf', o_dir_path_meth_est])
                    os.makedirs(o_dir_path_meth_est)

                    if cdx:
                        cur_predictions = '%s/predictions.qza' % o_dir_path_meth_est
                        cur_probabilities = '%s/probabilities.qza' % o_dir_path_meth_est
                        cur_predictions_d = splitext(cur_predictions)[0]
                        cur_probabilities_d = splitext(cur_probabilities)[0]

                        res.append([
                            t, r,
                            '%s.tsv' % cur_predictions_d,
                            '%s.tsv' % cur_probabilities_d,
                        ])

                        cmd += 'qiime sample-classifier predict-classification'
                        cmd += ' --i-table %s' % cur_qza
                        cmd += ' --i-sample-estimator %s' % sample_estimator
                        cmd += ' --p-n-jobs %s' % cur_p_cpus
                        cmd += ' --o-predictions %s' % cur_predictions
                        cmd += ' --o-probabilities %s\n' % cur_probabilities
                        cmd += 'qiime tools export --input-path %s --output-path %s\n' % (
                            cur_predictions, cur_predictions_d)
                        cmd += 'mv  %s/* %s.tsv\n' % (cur_predictions_d, cur_predictions_d)
                        cmd += 'qiime tools export --input-path %s --output-path %s\n' % (
                            cur_probabilities, cur_probabilities_d)
                        cmd += 'mv  %s/* %s.tsv\n' % (cur_probabilities_d, cur_probabilities_d)
                        cmd += 'rm -rf %s %s %s %s\n' % (cur_predictions, cur_predictions_d,
                                                             cur_probabilities, cur_probabilities_d)
                    else:
                        sample_estimator = '%s/sample_estimator.qza' % o_dir_path_meth_est
                        feature_importance = '%s/feature_importance.qza' % o_dir_path_meth_est
                        model_summary = '%s/model_summary.qzv' % o_dir_path_meth_est
                        predictions = '%s/predictions.qza' % o_dir_path_meth_est
                        accuracy_results = '%s/accuracy_results.qzv' % o_dir_path_meth_est
                        probabilities = '%s/probabilities.qza' % o_dir_path_meth_est
                        heatmap = '%s/heatmap.qzv' % o_dir_path_meth_est
                        accuracy_results_d = splitext(accuracy_results)[0]

                        cmd += 'qiime sample-classifier classify-samples'
                        cmd += ' --i-table %s' % cur_qza
                        cmd += ' --m-metadata-file %s' % map_out
                        cmd += ' --m-metadata-column Env'
                        cmd += ' --p-cv 1'
                        cmd += ' --p-n-jobs %s' % cur_p_cpus
                        cmd += ' --p-estimator %s' % estimator
                        cmd += ' --o-sample-estimator %s' % sample_estimator
                        cmd += ' --o-feature-importance %s' % feature_importance
                        cmd += ' --o-predictions %s' % predictions
                        cmd += ' --o-model-summary %s' % model_summary
                        cmd += ' --o-accuracy-results %s' % accuracy_results
                        cmd += ' --o-probabilities %s' % probabilities
                        cmd += ' --o-heatmap %s\n' % heatmap

                        cmd += 'qiime tools export --input-path %s --output-path %s\n' % (
                            accuracy_results, accuracy_results_d)
                        cmd += 'mv  %s/predictions.pdf %s_confusion.pdf\n' % (accuracy_results_d, accuracy_results_d)
                        cmd += 'mv  %s/roc_plot.pdf %s_roc.pdf\n' % (accuracy_results_d, accuracy_results_d)
                        cmd += 'tail -n 3 %s/predictive_accuracy.tsv > %s.tsv\n' % (accuracy_results_d, accuracy_results_d)

                        cmd += 'rm -rf %s %s %s %s %s\n' % (feature_importance, predictions, probabilities,
                                                          accuracy_results, accuracy_results_d)
                cmd += 'rm -rf %s %s\n' % (map_out, cur_qza)
    return cmd
