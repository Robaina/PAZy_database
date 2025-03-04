# PAZy Database Web Scraper

## Overview

This Python script scrapes enzyme information from the [PAZy Database](https://pazy.eu), specifically designed to collect biochemically characterized plastic-active enzymes. The script performs the following tasks:

- Fetches polymer type links (e.g., PET, PUR, PLA) from the PAZy landing page.
- Visits each polymer-specific page and retrieves detailed enzyme metadata such as the organism, enzyme name, EC number, relevant references, and UniProt accession ID.
- Correctly extracts polymer IDs from abbreviations in parentheses (e.g., "PLA" from "Polylactic acid (PLA)").
- Automatically retrieves enzyme sequences from UniProt based on accession IDs.
- Stores the extracted enzyme metadata in a tab-separated values (TSV) file (`PAZy_metadata.tsv`).
- Saves enzyme sequences in FASTA format in a separate file (`PAZy_sequences.fasta`).

## Requirements

Install the required packages with:

```bash
pip install -r requirements.txt
```

## How to Use

Run the script from your command line with optional arguments:

```bash
python pazy_scraper.py [--output OUTPUT_DIR] [--log LOG_FILE]
```

### Command-line Arguments

- `--output`: Path to the output directory (default: current directory)
- `--log`: Path to the log file (optional)

### Example Usage

```bash
# Basic usage (outputs to current directory)
python pazy_scraper.py

# Specify output directory
python pazy_scraper.py --output data/

# Specify log file
python pazy_scraper.py --log scraper.log

# Specify both output directory and log file
python pazy_scraper.py --output data/ --log logs/scraper.log
```

Upon completion, two files are generated:

- **`PAZy_metadata.tsv`**: Contains enzyme details (polymer type, polymer ID, organism, enzyme name, EC number, references, and database ID).
- **`PAZy_sequences.fasta`**: Contains the corresponding enzyme sequences in FASTA format with headers including internal ID and polymer ID.

## Polymer ID Extraction

The script intelligently extracts polymer IDs:
- First attempts to find abbreviations in parentheses (e.g., "PLA" from "Polylactic acid (PLA)")
- Falls back to special cases for common polymers (PET, PUR)
- If no abbreviation is found, uses the first three letters of the polymer name

## Sequence Prefix Meaning (UniProt FASTA headers)

Sequences retrieved from UniProt have headers starting with prefixes:

- `>sp`: Indicates the sequence is from the **Swiss-Prot** database, representing manually reviewed entries.
- `>tr`: Indicates the sequence is from **TrEMBL**, representing automatically annotated, unreviewed entries.

### Example FASTA Entries

```fasta
>sp|F7IX06|PETH2_THEAE Cutinase est2 OS=Thermobifida alba OX=53522 GN=est2 PE=1 SV=1
MSVTTPRRETSLLSRALRATAAAATAVVATVALAAPAQAANPYERGPNPTESMLEARSGPFSVSEERASRFGADGFGGGTIYYPRENNTYGAIAISPGYTGTQSSIAWLGERIASHGFVVIAIDTNTTLDQPDSRARQLNAALDYMLTDASSAVRNRIDASRLAVMGHSMGGGGTLRLASQRPDLKAAIPLTPWHLNKSWRDITVPTLIIGAEYDTIASVTLHSKPFYNSIPSPTDKAYLELDGASHFAPNITNKTIGMYSVAWLKRFVDEDTRYTQFLCPGPRTGLLSDVEEYRSTCPF

>tr|A0A1E1FNX8|A0A1E1FNX8_BACPU PBAT hydrolase OS=Bacillus pumilus OX=1408 GN=pbath PE=4 SV=1
MKVILFKKRSLQILVALALVIGSMAFIQPKEVKAAEHNPVVMVHGIGGASYNFASIKSYLVGQGWDRNQLYAIDFIDKTGNNRNNGPRLSKFVQDVLDKTGAKKVDIVAHSMGGANTLYYIKNLDGGDKIENVVTIGGANGLVSSRALPGTDPNQKILYTSVYSSADLIVVNSLSRLIGAKNVLIHGVGHIGLLTSSQVKGYIKEGLNGGGQNTN
```

## Notes

- SSL certificate warnings are intentionally suppressed (`verify=False`) to handle SSL certificate verification issues with PAZy.
- The script includes polite scraping practices by implementing delays between requests to avoid overloading the servers.
- Robust error handling and retry logic are implemented to handle intermittent connection issues.

## Disclaimer

Use responsibly and ensure your scraping practices comply with the PAZy and UniProt terms of service.