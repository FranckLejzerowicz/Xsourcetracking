# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd


def get_metadata(m_metadata: str, p_column_name: str,
                 p_sources: tuple, p_sink: str) -> (pd.DataFrame, str, list, str):
    with open(m_metadata) as f:
        for line in f:
            break
    metadata = pd.read_csv(m_metadata, header=0, sep='\t', dtype={line.split('\t')[0]: str})
    metadata = metadata.rename(columns={metadata.columns.tolist()[0]: 'sample_name'})
    metadata.columns = [x.replace('\n', '') for x in metadata.columns]
    if p_column_name not in metadata.columns.tolist()[1:]:
        raise IOError('"%s" not in "%s"' % (p_column_name, m_metadata))
    metadata_factors = metadata[p_column_name].unique().tolist()
    if p_sink not in metadata_factors:
        raise IOError('Sink "%s" not in "%s" column "%s"' % (p_sink, m_metadata, p_column_name))
    if p_sources:
        sources = []
        for p_source in p_sources:
            if p_source not in metadata_factors:
                raise IOError('Source "%s" not in "%s" column "%s"' % (p_source, m_metadata, p_column_name))
            sources.append(p_source)
    else:
        sources = [x for x in metadata_factors if str(x) not in ['nan', p_sink]]
    return metadata, p_column_name, sources, p_sink
