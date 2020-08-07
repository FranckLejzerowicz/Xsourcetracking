# ----------------------------------------------------------------------------
# Copyright (c) 2020, Franck Lejzerowicz.
#
# Distributed under the terms of the MIT License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import click

from Xsourcetracking.xsourcetracking import xsourcetracking
from Xsourcetracking import __version__


@click.command()
@click.option(
    "-i", "--i-table", required=True, type=str,
    help="Features table."
)
@click.option(
    "-o", "--o-dir-path", required=True, type=str,
    help="Output directory path."
)
@click.option(
    "-m", "--m-metadata", required=True, type=str,
    help="Sample metadata table."
)
@click.option(
    "-fc", "--p-column", required=False, type=str,
    default=None, help="Column from metadata `-m` to use for "
                       "filtering based on values of `-v`."
)
@click.option(
    "-fv", "--p-column-value", required=False, type=str, multiple=True,
    default=None, help="Filtering value to select samples based"
                       " on column passed to `-c`."
)
@click.option(
    "-fq", "--p-column-quant", required=False, type=int,
    default=0, help="Filtering quantile / percentile for samples based on"
                    " column passed to `-c` (must be between 0 and 100)."
)
@click.option(
    "-fp", "--p-filter-prevalence", required=False, type=float,
    default=0, help="Filter features based on their minimum sample prevalence "
                    "(number >1 for sample counts: <1 for samples fraction)."
)
@click.option(
    "-fa", "--p-filter-abundance", required=False, type=float,
    default=0, help="Filter features based on their minimum sample abundance "
                    "(number >1 for abundance counts: <1 for abundance fraction)."
)
@click.option(
    "-fo", "--p-filter-order", required=False, default='meta-filter',
    type=click.Choice(['meta-filter', 'filter-meta']),
    show_default=True, help="Order to apply the filters: 'filter-meta' first the prevalence/"
                            "abundance and then based on variable; 'meta-filter' first based "
                            "on variable and then the prevalence/abundance on the remaining."
)
@click.option(
    "-c", "--p-column-name", required=True, type=str,
    help="Sample metadata column to check."
)
@click.option(
    "-si", "--p-sink", required=True, type=str,
    help="[feast/sourcetracker] factor in a the metadata column"
         " passed to `-c` to use for labeling check."
)
@click.option(
    "-so", "--p-sources", required=False, type=str, multiple=True, default=None,
    help="[feast/sourcetracker] Presumed source factor(s) table column to use " 
         "for labeling check (default to all factors except that passed to `-si`)."
)
@click.option(
    "-n", "--p-iterations-burnins", required=False, type=int,
    default=None, help="[feast] number of EM iterations,"
                       "[sourcetracker] number of burn-ins."
)
@click.option(
    "-r", "--p-rarefaction", required=False, type=int,
    default=None, help="[feast/sourcetracker] rarefaction depth."
)
@click.option(
    "-meth", "--p-method", required=False, default='feast',
    type=click.Choice(['feast', 'sourcetracker', 'q2', 'metastorms', 'classify']),
    help="Method for labeling check."
)
@click.option(
    "-j", "--p-cpus", required=False, default=1, type=int,
    help="[sourcetracker] Number of cpus/jobs."
)
@click.option(
    "-s", "--p-size", required=False, default=None, type=float,
    help="Percent / Number of samples per prediction."
)
@click.option(
    "-h", "--p-chunks", required=False, default=None, type=int,
    help="Number of chunks to split the sink samples into."
)
@click.option(
    "-t", "--p-times", required=False, type=int, default=1,
    help="[feast/sourcetracker] number of times to make selections."
)
@click.option(
    "--diff-sources", "--no-diff-sources", default=False,
    help="[feast] Indicate the source-sink assignment. "
         "Set if different sources are assigned "
         "to each sink, do not set otherwise."
)
@click.option(
    "--run", "--no-run", default=False,
    help="Whether the commands should be run "
         "(e.g. or to be used by a third party handler)"
)
@click.option(
    "--verbose/--no-verbose", default=False
)
@click.version_option(__version__, prog_name="Xsourcetracking")
def standalone_xsourcetracking  (
        i_table,
        o_dir_path,
        m_metadata,
        p_column,
        p_column_value,
        p_column_quant,
        p_filter_prevalence,
        p_filter_abundance,
        p_filter_order,
        p_column_name,
        p_sources,
        p_sink,
        p_iterations_burnins,
        p_rarefaction,
        p_method,
        p_cpus,
        p_size,
        p_chunks,
        p_times,
        diff_sources,
        verbose,
        run
):

    xsourcetracking(
        i_table,
        o_dir_path,
        m_metadata,
        p_column,
        p_column_value,
        p_column_quant,
        p_filter_prevalence,
        p_filter_abundance,
        p_filter_order,
        p_column_name,
        p_sources,
        p_sink,
        p_iterations_burnins,
        p_rarefaction,
        p_method,
        p_cpus,
        p_size,
        p_chunks,
        p_times,
        diff_sources,
        verbose,
        run
    )


if __name__ == "__main__":
    standalone_xsourcetracking()
