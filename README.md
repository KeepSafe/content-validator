content-validator
=================

Content validator looks at text content and preforms different validation tasks.

## Requirements

1. Python 2.7.+

## Installation

`make install`

## Usage

Type `content-validator -h` and `content-validator [dir_path]` to see help message in the console.

If run without any parameters except the path it will throw an exception if there are any problems with the content.

### Output file

In case an output file is provided invalid urls will be saved to the output file, one per line.

### Input file

An input file has the following structure:

```
link_invalid_1 => link_valid_1
link_invalid_2 => link_valid_4
```

In that case `link_invalid_1` and `link_invalid_2` will be replaced by `link_valid_1` and `link_valid_2` respectively.

If you don't want a link to be replaced leave it on a separate line:

```
link_invalid_1 => link_valid_1
link_keep_1
```

### Filter

In case only files matching specific pattern should be processed, use `-f` flag with normal unix style pattern, like `*.csv`

## Workflow

The usual workflow for this tool is the following:

1. Set up an automatic process to run the tool on content change without any parameters except the path.
2. If the script throws any exceptions, run it with the output file specified.
3. Edit the output file and provide valid values which should replace the invalid ones.
4. Run the tool with an input file parameter.