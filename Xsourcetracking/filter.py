# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd


def num_filter(otu: pd.DataFrame,
               p_filter_prevalence: float,
               p_filter_abundance: float) -> pd.DataFrame:
    preval, abund = p_filter_prevalence, p_filter_abundance
    otu_filt = otu.copy()
    # get the min number of samples based on prevalence percent
    if preval < 1:
        n_percent = otu.shape[1] * preval
    else:
        n_percent = preval
    # abundance filter in terms of min reads counts
    otu_percent = otu_filt.copy()
    otu_percent_sum = otu_filt.sum(1)
    if abund < 1:
        otu_percent = otu_filt / otu_filt.sum()
        otu_percent_sum = otu_filt.sum(1) / otu_filt.sum(1).sum()

    abund_mode = 'sample'

    # remove features from feature table that are not present
    # in enough samples with the minimum number/percent of reads in these samples
    if abund_mode == 'sample':
        otu_filt = otu_filt.loc[(otu_percent > abund).sum(1) > n_percent, :]
    elif abund_mode == 'dataset':
        otu_filt = otu_filt.loc[otu_percent_sum > abund, :]
    elif abund_mode == 'both':
        otu_filt = otu_filt.loc[(otu_percent > abund).sum(1) > n_percent, :]
        fil_pd_percent_sum = otu_filt.sum(1)
        if abund < 1:
            fil_pd_percent_sum = otu_filt.sum(1) / otu_filt.sum(1).sum()
        otu_filt = otu_filt.loc[fil_pd_percent_sum > abund, :]
    else:
        raise Exception('"%s" mode not recognized' % abund_mode)
    otu_filt = otu_filt.loc[otu_filt.sum(1) > 0, otu_filt.sum(0) > 0]
    return otu_filt


def get_metadata(m_metadata: str) -> pd.DataFrame:
    with open(m_metadata) as f:
        for line in f:
            break
    meta = pd.read_csv(
        m_metadata, header=0, sep='\t',
        dtype={line.split('\t')[0]: str}
    )
    meta = meta.rename(columns={meta.columns.tolist()[0]: 'sample_name'})
    meta.columns = [x.replace('\n', '') for x in meta.columns]
    return meta


def get_sign_val(p_omic_value: str) -> list:
    signs_vals = []
    for p_omic_val in p_omic_value:
        if p_omic_val[:2] in ['<=', '>=']:
            sign = p_omic_val[:2]
            val = p_omic_val[2:]
        elif p_omic_val[0] in ['<', '>']:
            sign = p_omic_val[0]
            val = p_omic_val[1:]
        try:
            signs_vals.append([sign, float(val)])
        except TypeError:
            raise TypeError('%s in %s must be numeric' % (val, p_omic_value))
    return signs_vals


def get_col_bool_sign(meta_col: pd.Series, signs_vals: list) -> pd.Series:

    if signs_vals[0][0] == '<':
        meta_bool = meta_col.astype(float) < signs_vals[0][1]
    elif signs_vals[0][0] == '>':
        meta_bool = meta_col.astype(float) > signs_vals[0][1]
    elif signs_vals[0][0] == '<=':
        meta_bool = meta_col.astype(float) <= signs_vals[0][1]
    elif signs_vals[0][0] == '>=':
        meta_bool = meta_col.astype(float) >= signs_vals[0][1]
    else:
        raise IOError("Sign %s none of ['<', '>', '<=', '>=']" % signs_vals[0][0])

    if len(signs_vals) == 2:
        if signs_vals[1][0] == '<':
            meta_bool2 = meta_col.astype(float) < signs_vals[1][1]
        elif signs_vals[1][0] == '>':
            meta_bool2 = meta_col.astype(float) > signs_vals[1][1]
        elif signs_vals[1][0] == '<=':
            meta_bool2 = meta_col.astype(float) <= signs_vals[1][1]
        elif signs_vals[1][0] == '>=':
            meta_bool2 = meta_col.astype(float) >= signs_vals[1][1]
        else:
            raise IOError("Sign %s none of ['<', '>', '<=', '>=']" % signs_vals[1][0])
        return meta_bool & meta_bool2
    else:
        return meta_bool


def cat_filter(tab: pd.DataFrame, metadata: pd.DataFrame,
               p_column: str, p_column_value: tuple,
               p_column_quant: int) -> pd.DataFrame:

    if p_column not in metadata.columns.tolist()[1:]:
        raise IOError('Variable "%s" not in metadata"' % p_column)
    elif p_column.replace('\\n', '') in metadata.columns:
        p_column = p_column.replace('\\n', '')

    meta_col = metadata[p_column].copy()
    if p_column_quant:
        if p_column_quant < 0 or p_column_quant > 100:
            raise IOError('Quantile must be between 0 and 100, not', p_column_quant)
        if str(meta_col.dtype) == 'float64':
            q = meta_col.quantile(q=p_column_quant / 100)
            meta_col = meta_col[meta_col > q]
            metadata = metadata.loc[meta_col.index, :]
    if p_column_value:
        if len([1 for x in p_column_value if x[0] in ['<', '>']]):
            signs_vals = get_sign_val(p_column_value)
            filt = get_col_bool_sign(meta_col, signs_vals)
        else:
            if not len([x for x in p_column_value if x in meta_col.values]):
                raise IndexError('None of "%s" in column "%s"' % (', '.join(list(p_column_value)), p_column))
            filt = meta_col.isin([x for x in p_column_value])
        metadata = metadata[filt]

    tab = tab.loc[:, list(set(metadata.sample_name) & set(tab.columns))]
    return tab


def do_filter(tab: pd.DataFrame,
              metadata: pd.DataFrame,
              p_filter_prevalence: float,
              p_filter_abundance: float,
              p_filter_order: str,
              p_column: str,
              p_column_value: tuple,
              p_column_quant: int) -> pd.DataFrame:

    if p_filter_order == 'meta-filter':
        if p_column_value or p_column_quant:
            tab = cat_filter(tab, metadata, p_column, p_column_value, p_column_quant)
        if p_filter_prevalence or p_filter_abundance:
            tab = num_filter(tab, p_filter_prevalence, p_filter_abundance)
    else:
        if p_filter_prevalence or p_filter_abundance:
            tab = num_filter(tab, p_filter_prevalence, p_filter_abundance)
        if p_column_value or p_column_quant:
            tab = cat_filter(tab, metadata, p_column, p_column_value, p_column_quant)
    return tab

