# PAZy Database Web Scraper

## Overview

This Python script scrapes enzyme information from the [PAZy Database](https://pazy.eu), specifically designed to collect biochemically characterized plastic-active enzymes. The script performs the following tasks:

- Fetches polymer type links (e.g., PET, PUR, PLA) from the PAZy landing page.
- Visits each polymer-specific page and retrieves detailed enzyme metadata such as the organism, enzyme name, EC number, relevant references, and UniProt accession ID.
- Automatically retrieves enzyme sequences from UniProt based on accession IDs.
- Stores the extracted enzyme metadata in a tab-separated values (TSV) file (`PAZy_metadata.tsv`).
- Saves enzyme sequences in FASTA format in a separate file (`PAZy_sequences.fasta`).

## Requirements

Ensure you have Python installed. You need the following Python packages:

```bash
requests
beautifulsoup4
```

Install the required packages with:

```bash
pip install -r requirements.txt
```

## How to Use

Simply run the script from your command line:

```bash
python pazy_scraper.py
```

Upon completion, two files are generated:

- **`PAZy_metadata.tsv`**: Contains enzyme details (polymer type, organism, enzyme name, EC number, references, and UniProt ID).
- **`PAZy_sequences.fasta`**: Contains the corresponding enzyme sequences in FASTA format.

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

## Disclaimer

Use responsibly and ensure your scraping practices comply with the PAZy and UniProt terms of service.

