# layrex

A malware analysis sandbox tool chain leveraging container technology

## Installation

```bash
pip install .
```

## Usage

### Binary Analysis

```bash
layrex run <INPUT_DIR> <OUTPUT_DIR>
```

* `INPUT_DIR`: input directory containing all the target binaries.
* `OUTPUT_DIR`: output directory to dump the JSON report file.

### Report Dumping

Information will be lost in dumping. Dumped format is a selected subset of the input JSON report file depending on the target format chosen.

```bash
layrex dump <REPORT_FILE>  -o <OURPUT_DIR>  -f [files|markdown]
```

* `REPORT_FILE`: path to the JSON report file.
* `OURPUT_DIR`: output directory
* `FORMAT`: the target file format
  * `files` will tell layrex to dump all the filesystem/network activities to a directory.
  * `markdown` will tell layrex to dump the report in markdown.