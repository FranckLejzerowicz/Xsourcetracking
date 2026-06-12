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

from Xsourcetracking.utils import (
    get_chunks_set, get_chunks, make_dirs, write_cur_meta, get_cpus,
    check_folder
)
from Xsourcetracking.sourcesink import get_chunk_nsources, get_timechunk_meta


def get_pred_map(o_dir, chunk, sink) -> str:
    map_out = '%s/map.prediction.tsv' % o_dir
    with open(map_out, 'w') as o:
        o.write('#SampleID\tEnv\n')
        for c in chunk:
            o.write('%s\t%s\n' % (c, sink))
    return map_out


def get_tab_qza(tab_qza, map_out, cdx, o_dir, params, cmd_imp):
    if cdx:
        tab = '%s/tab.prediction' % o_dir
        raref = params.get('sink_rarefaction_depth')
    else:
        tab = '%s/tab.model' % o_dir
        raref = params.get('source_rarefaction_depth')
    filt_qza = '%s.qza' % tab
    if not isfile(filt_qza):
        cmd_imp += 'qiime feature-table filter-samples'
        cmd_imp += ' --i-table %s' % tab_qza
        cmd_imp += ' --m-metadata-file %s' % map_out
        cmd_imp += ' --o-filtered-table %s\n' % filt_qza
    if raref:
        qza = '%s_raref%s.qza' % (tab, raref)
        if not isfile(qza):
            cmd_imp += 'qiime feature-table rarefy'
            cmd_imp += ' --i-table %s' % filt_qza
            cmd_imp += ' --p-sampling-depth %s' % raref
            cmd_imp += ' --o-rarefied-table %s\n' % (tab, qza)
    else:
        qza = filt_qza
    return tab, qza


def write_predict_cmd(qza, est, chunk, p_cpus, out, cmd):
    cmd += 'cd %s\n' % out
    cmd += 'qiime sample-classifier predict-classification'
    cmd += ' --i-table %s' % qza
    cmd += ' --i-sample-estimator %s' % est_qza
    cmd += ' --o-predictions predictions.qza'
    cmd += ' --o-probabilities probabilities.qza'
    cmd += ' --p-n-jobs %s\n' % get_cpus(chunk, p_cpus)

    cmd += 'qiime tools export --input-path predictions.qza --output-path pr\n'
    cmd += 'mv  pr/* predictions.tsv\n'

    cmd += 'qiime tools export --input-path probabilities.qza --output-path p\n'
    cmd += 'mv  p/* probabilities.tsv\n'

    cmd += 'rm -rf p pb predictions.qza probabilities.qza \n'


def write_model_cmd(qza, e, map_out, chunk, p_cpus, out, cmd):
    est_qza = '%s/sample_estimator.qza' % out
    feat_qza = '%s/feature_importance.qza' % out
    mod_sum = '%s/model_summary.qzv' % out
    pred_qza = '%s/predictions.qza' % out
    prob_qza = '%s/probabilities.qza' % out
    heat_qza = '%s/heatmap.qzv' % out
    acc = '%s/accuracy_results' % out

    cmd += 'qiime sample-classifier classify-samples'
    cmd += ' --i-table %s' % qza
    cmd += ' --m-metadata-file %s' % map_out
    cmd += ' --m-metadata-column Env'
    cmd += ' --p-cv 1'
    cmd += ' --p-n-jobs %s' % get_cpus(chunk, p_cpus)
    cmd += ' --p-estimator %s' % e
    cmd += ' --o-sample-estimator %s' % est_qza
    cmd += ' --o-feature-importance %s' % feat_qza
    cmd += ' --o-predictions %s' % pred_qza
    cmd += ' --o-model-summary %s' % mod_sum
    cmd += ' --o-accuracy-results %s.qzv' % acc
    cmd += ' --o-probabilities %s' % prob_qza
    cmd += ' --o-heatmap %s\n' % heat_qza

    cmd += 'qiime tools export'
    cmd += ' --input-path %s.qzv' % acc
    cmd += ' --output-path %s\n' % acc

    cmd += 'mv  %s/predictions.pdf %s_confusion.pdf\n' % (acc, acc)
    cmd += 'mv  %s/roc_plot.pdf %s_roc.pdf\n' % (acc, acc)
    cmd += 'tail -n 3 %s/predictive_accuracy.tsv > %s.tsv\n' % (acc, acc)

    cmd += 'rm -rf %\n' % acc


def run_q2classifier(
        tab_out: str,
        dir_out: str,
        samples: dict,
        counts: dict,
        sources: tuple,
        sink: str,
        p_chunks: int,
        p_cpus: int,
        params: dict
) -> str:
    res = []
    tool = 'q2_classifier'
    cmd, cmd_imp = '', ''
    tab_biom = '%s.biom' % splitext(tab_out)[0]
    tab_qza = '%s.qza' % splitext(tab_out)[0]
    if not isfile(tab_qza):
        cmd_imp += 'biom convert -i %s -o %s' % (tab_out, tab_biom)
        cmd_imp += ' --to-hdf5 --table-type="OTU table"\n'
        cmd_imp += 'qiime tools import --input-path %s --output-path' % tab_biom
        cmd_imp += ' %s --type FeatureTable[Frequency]\n' % tab_qza

    for t in range(params['times']):
        chunks_set = get_chunks_set(samples, sink, p_chunks, params['size'])
        for r in range(len(chunks_set)):
            chunks = get_chunks(chunks_set, r, True)
            for cdx, chunk in enumerate(chunks):
                if cdx:
                    map_out = get_pred_map(o_dir, chunk, sink)
                else:
                    o_dir = make_dirs(dir_out, t, r)
                    map_out, _ = write_cur_meta(
                        o_dir, chunk, sources, sink, counts,
                        samples, 'q2_classifier', r)
                tab, qza = get_tab_qza(
                    tab_qza, map_out, cdx, o_dir, params, cmd_imp)
                for e in params['estimators']:
                    out = o_dir + '/%s' % e
                    check_folder(out, tool, cmd)
                    os.makedirs(out)
                    if cdx:
                        write_predict_cmd(qza, est_qza, chunk, p_cpus, out, cmd)
                        pred = '%s/predictions' % out
                        prob = '%s/probabilities' % out
                        res.append([t, r, e, pred + '.tsv', prob + '.tsv'])
                    else:
                        write_model_cmd(qza, e, map_out, chunk, p_cpus, out, cmd)
                cmd += 'rm -rf %s %s\n' % (map_out, cur_qza)
    return cmd