import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import warnings
from urllib3.exceptions import InsecureRequestWarning
import argparse
import logging
import os
import re  # Added for regex pattern matching

# Disable SSL warnings (as in the original script)
warnings.simplefilter("ignore", InsecureRequestWarning)


def setup_argparse():
    parser = argparse.ArgumentParser(
        description="Scrape polymer enzyme data from PAZy database."
    )
    parser.add_argument("--log", help="Path to the log file")
    parser.add_argument(
        "--output",
        help="Path to the output directory (default: current directory)",
        default=".",
    )
    return parser.parse_args()


def setup_logging(log_path=None):
    logger = logging.getLogger("pazy_scraper")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # File handler (if log path provided)
    if log_path:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def perform_request_with_retries(url, logger, max_retries=3, base_delay=1):
    """Fetches URL text with retries and exponential backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Attempt {attempt}: Error fetching {url}: {e}")
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying after {delay} seconds...")
                time.sleep(delay)
    logger.error(f"Failed to fetch URL: {url} after {max_retries} attempts.")
    return None


def fetch_polymer_links(base_url, landing_url, logger):
    logger.info(f"Fetching polymer links from {landing_url}")
    response_text = perform_request_with_retries(
        landing_url, logger, max_retries=5, base_delay=1
    )
    if not response_text:
        logger.error("Failed to retrieve landing page.")
        return []
    soup = BeautifulSoup(response_text, "html.parser")
    table = soup.find("table", {"class": "inline"})
    polymer_links = []
    if table:
        for a in table.find_all("a", {"class": "wikilink1"}):
            href = a.get("href")
            if href and "id=" in href:
                full_url = urljoin(base_url, href)
                polymer_name = a.get_text(strip=True)
                polymer_links.append((polymer_name, full_url))
    logger.info(f"Found {len(polymer_links)} polymer types")
    return polymer_links


def fetch_enzyme_data(polymer_name, polymer_url, logger):
    logger.info(f"Processing polymer: {polymer_name}")
    enzyme_data = []
    page_text = perform_request_with_retries(
        polymer_url, logger, max_retries=3, base_delay=1
    )
    if not page_text:
        logger.error(f"Failed to retrieve {polymer_name} page.")
        return enzyme_data

    soup = BeautifulSoup(page_text, "html.parser")
    table = soup.find("table", {"class": "inline"})
    if not table:
        logger.warning(f"No table found on {polymer_name} page.")
        return enzyme_data

    # FIX: Improved polymer_id extraction
    # Look for abbreviation in parentheses first
    abbr_match = re.search(r"\(([A-Z]+)\)", polymer_name)
    if abbr_match:
        polymer_id = abbr_match.group(1)
    elif polymer_name.lower().startswith("polyethylene terephthalate"):
        polymer_id = "PET"
    elif polymer_name.lower().startswith("polyurethane"):
        polymer_id = "PUR"
    else:
        polymer_id = polymer_name[:3].upper()

    rows = table.find_all("tr")
    for row in rows[1:]:  # Skip header row explicitly
        cells = row.find_all(["td", "th"])
        if len(cells) < 6:
            continue  # Skip incomplete or header rows
        host_enzyme_gene = cells[0].get_text(separator=" ", strip=True)
        ec_number = cells[1].get_text(strip=True)
        references = "; ".join(a.get_text(strip=True) for a in cells[2].find_all("a"))
        id_cell = cells[3]

        # Extract Database ID and type
        db_type, database_id, database_link = "", "", ""
        for a in id_cell.find_all("a"):
            href = a.get("href", "")
            if "uniprot" in href.lower():
                db_type = "UniProt"
                database_id = a.get_text(strip=True).split("_")[0]
                database_link = href
                break
            elif "genbank" in href.lower() or "ncbi.nlm.nih.gov" in href.lower():
                db_type = "GenBank"
                database_id = a.get_text(strip=True)
                database_link = href
                break
            elif (
                "ebi.ac.uk" in href.lower() or "mgyp" in a.get_text(strip=True).lower()
            ):
                db_type = "MGnify"
                database_id = a.get_text(strip=True)
                database_link = href
                break
            else:
                db_type = ""
                database_id = ""
                database_link = ""
        # Handle organism and enzyme_name extraction
        organism = ""
        enzyme_name = ""
        if "," in host_enzyme_gene:
            organism, enzyme_name = [
                part.strip() for part in host_enzyme_gene.split(",", 1)
            ]
        else:
            organism = host_enzyme_gene

        enzyme_data.append(
            {
                "polymer": polymer_name,
                "polymer_id": polymer_id,
                "organism": organism,
                "enzyme_name": enzyme_name,
                "ec_number": ec_number,
                "references": references,
                "database_type": db_type,
                "database_id": database_id,
                "database_link": database_link,
            }
        )
        time.sleep(1)
    logger.info(f"Found {len(enzyme_data)} enzyme entries for {polymer_name}")
    return enzyme_data


def fetch_fasta(database_type, database_id, logger):
    logger.info(f"Fetching FASTA for {database_id} from {database_type}")
    if database_type == "UniProt":
        # Use UniProt REST endpoint for improved reliability
        fasta_url = f"https://rest.uniprot.org/uniprotkb/{database_id}.fasta"
    elif database_type == "GenBank":
        # Use NCBI E-utilities (efetch) instead of the old sviewer URL
        fasta_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=protein&id={database_id}&rettype=fasta&retmode=text"
    elif database_type == "MGnify":
        fasta_url = (
            f"https://www.ebi.ac.uk/metagenomics/api/v1/sequences/{database_id}/fasta"
        )
    else:
        logger.warning(f"Unknown database type for ID: {database_id}")
        return ""
    fasta_text = perform_request_with_retries(
        fasta_url, logger, max_retries=3, base_delay=1
    )
    return fasta_text if fasta_text else ""


def main():
    args = setup_argparse()
    logger = setup_logging(args.log)

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    base_url = "https://pazy.eu"
    landing_url = urljoin(base_url, "doku.php?id=start")

    logger.info("Starting PAZy database scraping")
    polymer_links = fetch_polymer_links(base_url, landing_url, logger)

    all_enzyme_data = []
    for polymer_name, polymer_url in polymer_links:
        enzymes = fetch_enzyme_data(polymer_name, polymer_url, logger)
        all_enzyme_data.extend(enzymes)
        time.sleep(2)

    # Process enzyme entries to fetch sequences and compile output
    successful_enzymes = []
    missing_sequence_count = 0
    internal_id_counter = 1
    sequences_output = ""

    for enzyme in all_enzyme_data:
        fasta_text = fetch_fasta(enzyme["database_type"], enzyme["database_id"], logger)
        if fasta_text:
            # Prepend internal ID to the FASTA header
            lines = fasta_text.splitlines()
            if lines and lines[0].startswith(">"):
                lines[0] = (
                    f">{internal_id_counter}|{enzyme['polymer_id']}_{lines[0][1:]}"
                )
            modified_fasta = "\n".join(lines)
            enzyme["fasta"] = modified_fasta
            enzyme["internal_id"] = str(internal_id_counter)
            internal_id_counter += 1
            successful_enzymes.append(enzyme)
            sequences_output += modified_fasta + "\n"
        else:
            missing_sequence_count += 1
            logger.warning(
                f"Sequence not found for enzyme: {enzyme['enzyme_name']} with ID: {enzyme['database_id']}"
            )
        time.sleep(1)

    # Write metadata output for enzymes with a valid sequence.
    metadata_file_path = os.path.join(output_dir, "PAZy_metadata.tsv")
    with open(metadata_file_path, "w", encoding="utf-8") as meta_file:
        meta_file.write(
            "Internal_ID\tPolymer\tPolymer_ID\tOrganism\tEnzyme Name\tEC Number\tReferences\tDatabase_Type\tDatabase_ID\n"
        )
        for enzyme in successful_enzymes:
            meta_row = [
                enzyme["internal_id"],
                enzyme["polymer"],
                enzyme["polymer_id"],
                enzyme["organism"],
                enzyme["enzyme_name"],
                enzyme["ec_number"],
                enzyme["references"],
                enzyme["database_type"],
                enzyme["database_id"],
            ]
            meta_file.write("\t".join(meta_row) + "\n")

    # Write FASTA sequences to file.
    fasta_file_path = os.path.join(output_dir, "PAZy_sequences.fasta")
    with open(fasta_file_path, "w", encoding="utf-8") as fasta_file:
        fasta_file.write(sequences_output)

    logger.info(
        f"Scraping complete. Metadata saved to {metadata_file_path} and sequences to {fasta_file_path}."
    )
    logger.info(
        f"{missing_sequence_count} PAZy entries without matching sequence were found."
    )


if __name__ == "__main__":
    main()
