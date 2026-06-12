# Xsourcetracking

**Xsourcetracking** is a Python command-line tool for microbial source tracking and sample label curation. Given a feature (OTU/ASV) table, a sample metadata file, and a metadata column that distinguishes sink samples from source samples, it orchestrates one of several statistical or machine-learning methods to estimate the most likely origin of features in each sink sample.

It wraps FEAST, QIIME 2's classify-samples, and (experimentally) metastorms and scikit-learn classifiers into a single, consistent CLI interface.

---

## Table of Contents

1. [Use cases](#use-cases)
2. [Installation](#installation)
3. [Conceptual overview](#conceptual-overview)
4. [Inputs](#inputs)
5. [Outputs](#outputs)
6. [CLI reference](#cli-reference)
7. [Methods](#methods)
8. [Filtering options](#filtering-options)
9. [Chunking and repeated sampling](#chunking-and-repeated-sampling)
10. [Examples](#examples)
11. [Notes and caveats](#notes-and-caveats)
12. [Bug reports](#bug-reports)

---

## Use cases

- Verify or audit metadata labels: identify sink samples whose community composition is better explained by a different source category.
- Quantify contamination or cross-environment signals in amplicon datasets.
- Explore mixing proportions of multiple potential source environments for a set of query (sink) samples.

---

## Installation

```bash
pip install -U git+https://github.com/FranckLejzerowicz/Xsourcetracking.git
```

**Python requirement:** >= 3.5

**Method-specific dependencies** (must be installed separately):

| Method | Dependency | Notes |
|---|---|---|
| `feast` | [FEAST](https://github.com/cozygene/FEAST) | R package; activate via `conda activate feast` |
| `q2` | QIIME 2 with `sample-classifier` plugin | — |
| `classify` | scikit-learn >= 0.22.2 | installed automatically |
| `metastorms` | scikit-learn >= 0.22.2 | experimental; not fully implemented |

The tool itself requires `click >= 6.7`, `pandas >= 0.19.0`, and `scikit-learn >= 0.22.2`. These are listed as `install_requires` in `setup.py` and will be installed automatically.

---

## Conceptual overview

Source tracking asks: *given that sample X is labelled as a "sink", how much of its microbial community can be attributed to known source environments?*

Xsourcetracking operationalises this by:

1. Reading a feature table (samples × features) and a metadata table.
2. Identifying sink samples (the samples whose labels you want to verify) and source samples (the reference communities) from a user-specified metadata column.
3. Optionally filtering features and/or samples.
4. Splitting sink samples into chunks and repeatedly drawing random subsets of source samples across multiple trials.
5. Writing per-trial feature tables and mapping files for the chosen method.
6. Generating a shell script (`cmd_<method>.sh`) that runs the method; optionally executing it immediately.

---

## Inputs

### Feature table (`-i` / `--i-table`)

A tab-separated feature table with features as rows and sample IDs as columns. The first column must be a feature identifier (e.g. OTU ID, ASV hash, or species name). Example:

```
featureid   sample1   sample2   sample3
ASV_001     120       0         45
ASV_002     0         300       10
```

The file must be tab-delimited. BIOM files are not accepted directly as input; convert to TSV first (`biom convert -i table.biom -o table.tsv --to-tsv`).

### Metadata table (`-m` / `--m-metadata`)

A tab-separated metadata file. The first column is treated as the sample identifier (regardless of its name); all other columns are metadata variables. Example:

```
#SampleID   sample_type   body_site   host_age
sample1     gut           colon       32
sample2     soil          garden      NA
sample3     gut           ileum       28
```

### Metadata source/sink column (`-c` / `--p-column-name`)

The name of the metadata column whose values distinguish sinks from sources. All unique values in this column (except `nan`) are treated as potential environment labels. The value passed to `-si` identifies the sink group; all others become sources unless restricted by `-so`.

---

## Outputs

All outputs are written under the directory passed to `-o` / `--o-dir-path`. The tool creates a structured subdirectory hierarchy based on the column name, sink label, and method:

```
<o-dir-path>/
└── <column_name>-<sink>/          # or <column_name>-<sink>_<source1>_<source2>
    ├── tab[_raref<depth>].tsv     # filtered/rarefied feature table (all samples)
    └── <method>/
        ├── cmd_<method>.sh        # generated shell script
        └── t0/                    # results for trial 0
            ├── map.r0.tsv         # metadata mapping file for chunk 0
            ├── map.r1.tsv         # metadata mapping file for chunk 1 (if applicable)
            └── <method output files>
```

If metadata-based filtering is applied (`-fc`, `-fv`, `-fq`), an additional subdirectory component is added:
```
<o-dir-path>/c-<filter_column>[-<values>][_p-<prevalence>][_a-<abundance>][_q-<quantile>]/
```

### Per-method output files

**FEAST** (`feast/tN/`):
- `out.rR_FEAST_output.txt` — mixing proportions per sink sample
- `out.rR_FEAST.log` — R log

**q2 / QIIME 2 classifier** (`q2/tN/`):
- Standard QIIME 2 classify-samples outputs

---

## CLI reference

```
Xsourcetracking [OPTIONS]
```

### Required arguments

| Flag | Long form | Description |
|---|---|---|
| `-i` | `--i-table` | Path to the feature table (TSV). |
| `-o` | `--o-dir-path` | Output directory. Created if it does not exist. |
| `-m` | `--m-metadata` | Path to the sample metadata (TSV). |
| `-c` | `--p-column-name` | Metadata column containing sink/source labels. |
| `-si` | `--p-sink` | Value in `-c` that identifies the **sink** group. |

### Method selection

| Flag | Long form | Default | Choices | Description |
|---|---|---|---|---|
| `-meth` | `--p-method` | `feast` | `feast`, `q2`, `metastorms`, `classify` | Source-tracking method to use. |

### Source definition

| Flag | Long form | Default | Description |
|---|---|---|---|
| `-so` | `--p-sources` | (all other values in `-c`) | One or more source labels from column `-c`. Repeatable: `-so gut -so soil`. If omitted, all non-sink values are used. |

### Method parameters

| Flag | Long form | Default | Description |
|---|---|---|---|
| `-n` | `--p-iterations-burnins` | None | For FEAST: number of EM iterations.
| `-r` | `--p-rarefaction` | None | Rarefaction depth. Samples with fewer reads are excluded. Appended to output table filename. |
| `-j` | `--p-cpus` | `1` | Number of parallel jobs. |
| `--diff-sources` / `--no-diff-sources` | | `--no-diff-sources` | FEAST only. Set if each sink uses a different set of source samples (`different_sources_flag=1`). |

### Execution

| Flag | Long form | Default | Description |
|---|---|---|---|
| `--run` / `--no-run` | | `--no-run` | If set, execute the generated shell script immediately. Otherwise only write it. |
| `--verbose` / `--no-verbose` | | `--no-verbose` | Print progress messages. |

### Chunking and sampling

| Flag | Long form | Default | Description |
|---|---|---|---|
| `-s` | `--p-size` | None | Chunk size as a fraction (0–1) or absolute count of sink samples per prediction batch. |
| `-h` | `--p-chunks` | None | Number of chunks to split sink samples into. Takes precedence over `-s`. |
| `-t` | `--p-times` | `1` | Number of independent trials (each trial draws a fresh random subset of source samples). |

### Sample filtering

| Flag | Long form | Default | Description |
|---|---|---|---|
| `-fc` | `--p-column` | None | Metadata column to filter samples on (used with `-fv` or `-fq`). |
| `-fv` | `--p-column-value` | None | Values to retain in the column given by `-fc`. Repeatable. Supports comparison operators: `>5`, `<=10`. |
| `-fq` | `--p-column-quant` | `0` | Keep only samples above this percentile (0–100) for the column given by `-fc`. Requires that column to be numeric. |
| `-fp` | `--p-filter-prevalence` | `0` | Minimum prevalence for features. Values >1 are treated as sample counts; values <1 as fractions. |
| `-fa` | `--p-filter-abundance` | `0` | Minimum abundance for features. Values >1 are treated as raw counts; values <1 as fractions. |
| `-fo` | `--p-filter-order` | `meta-filter` | Order of filters: `meta-filter` applies the metadata filter first, then prevalence/abundance; `filter-meta` reverses the order. |

---

## Methods

### FEAST (`-meth feast`)

[FEAST](https://github.com/cozygene/FEAST) is an R-based fast expectation-maximisation algorithm for source tracking. It estimates the proportion of each sink's microbiome attributable to each source.

Xsourcetracking generates an R script (`run_feast.R`) that calls `FEAST()` and writes it inside the method output directory, then wraps the invocation in a shell script using `source activate feast`.

Relevant parameters: `-n` (EM iterations), `-r` (coverage / rarefaction), `--diff-sources`.

### QIIME 2 classifier (`-meth q2`)

Wraps the QIIME 2 `sample-classifier` plugin's classification workflow. Metadata mapping files conforming to QIIME 2 format are generated per chunk and trial.

Relevant parameters: `-r`, `-j`.

### scikit-learn classifier (`-meth classify`)

A direct scikit-learn classification approach (currently under active development). Uses `train_test_split` from scikit-learn internally. The `classify` module is the least mature; check the source for current status.

### metastorms (`-meth metastorms`)

Experimental and not fully implemented in the current codebase. Not recommended for production use.

---

## Filtering options

Xsourcetracking supports two complementary types of filtering that can be applied before source tracking.

### Metadata-based sample filtering

Controlled by `-fc`, `-fv`, and `-fq`. To apply this, specify the metadata column to filter on with `-fc`. Then:

- Pass one or more categorical values with `-fv` to keep only samples matching those values (e.g. `-fv gut -fv colon`).
- Or pass a percentile with `-fq` to keep only samples with values above that quantile in a numeric column.
- For numeric columns, `-fv` also accepts comparison operators: `-fv ">5"`, `-fv "<=10"` (a range is defined by passing two such values).

### Feature-based filtering

Controlled by `-fp` (prevalence) and `-fa` (abundance):

- `-fp 0.1` removes features present in fewer than 10% of samples.
- `-fp 5` removes features present in fewer than 5 samples.
- `-fa 0.001` removes features whose per-sample abundance is below 0.1% in all samples.
- `-fa 10` removes features with fewer than 10 counts per sample in all samples.

### Filter ordering (`-fo`)

- `meta-filter` (default): apply metadata filter first, then feature filter on the remaining samples.
- `filter-meta`: apply feature filter first across all samples, then metadata filter.

If fewer than 10 features remain after filtering, the tool raises an error.

---

## Chunking and repeated sampling

For large datasets, or to obtain more robust estimates, sink samples can be split into batches and source samples can be randomly resampled multiple times.

**Chunking** (`-h` or `-s`):
- `-h 5` splits sink samples into 5 chunks of roughly equal size. Each chunk is run as a separate source-tracking job.
- `-s 0.2` creates chunks of 20% of the total sink count.
- `-s 100` creates chunks of 100 samples each.
- If neither is specified, the tool uses all sink samples in a single batch.

**Trials** (`-t`):
- `-t 10` runs 10 independent trials. Each trial draws a fresh random sample of source samples (up to the size of the current sink chunk) and outputs to a `tN/` subdirectory.
- Increasing trials gives a distribution of mixing proportions, enabling uncertainty estimation.

Sources are limited to groups with at least 20 samples; smaller groups are silently dropped.

---

## Examples

### Minimal FEAST run (generate script only)

```bash
Xsourcetracking \
  -i feature_table.tsv \
  -m metadata.tsv \
  -o results/ \
  -c sample_type \
  -si gut \
  --no-run
```

This will write `results/sample_type-gut/feast/cmd_feast.sh` without executing it.

### FEAST run with rarefaction, executed immediately

```bash
Xsourcetracking \
  -i feature_table.tsv \
  -m metadata.tsv \
  -o results/ \
  -c sample_type \
  -si gut \
  -so soil \
  -so water \
  -r 5000 \
  -n 1000 \
  -t 5 \
  --run \
  --verbose
```

Restricts sources to `soil` and `water`, rarefies to 5 000 reads, runs 1 000 EM iterations, repeats 5 times.

### Filtered run (prevalence + metadata filter)

```bash
Xsourcetracking \
  -i feature_table.tsv \
  -m metadata.tsv \
  -o results/ \
  -c sample_type \
  -si gut \
  -fc host_age \
  -fv ">18" \
  -fp 0.05 \
  -fa 0.001 \
  -fo meta-filter \
  --run
```

Keeps only samples from hosts older than 18, then removes features present at <5% prevalence or <0.1% relative abundance.

---

## Notes and caveats

**Source sample minimum.** Source groups with fewer than 20 samples are automatically excluded. If this leaves only one group (the sink), the tool exits with `Not enough source(s) samples`.

**Feature table format.** The table must be tab-separated with the feature identifier as the first column (named anything). Sample IDs must match between the table and the metadata. Mismatched samples are silently dropped at the intersection step.

**Script vs execution.** By default (`--no-run`), Xsourcetracking only generates shell scripts. This is useful for cluster submission workflows where you want to inspect or schedule the jobs manually before running them.

**Output directory naming.** The output path encodes the column name, sink label, and (if specified) the selected source labels. This means re-running with different source sets does not overwrite previous results.

**metastorms and classify methods.** These modules contain incomplete implementations (stubs and commented-out code). They generate a shell script placeholder but may raise errors or produce no meaningful output.

---

## Bug reports

Contact: `franckl@uio.no`

Or open an issue at https://github.com/FranckLejzerowicz/Xsourcetracking/issues
