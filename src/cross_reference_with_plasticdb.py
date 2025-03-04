#!/usr/bin/env python3
import argparse
from Bio import SeqIO
import hashlib
from collections import defaultdict
import time


def create_plasticdb_lookup(plasticdb_file, verify_exact=False, no_duplicates=False):
    """
    Create a lookup dictionary from sequence MD5 hash to PlasticDB IDs and descriptions.
    If verify_exact is True, the actual sequences are also stored.
    If no_duplicates is True, only the first occurrence of each unique sequence is kept.
    """
    seq_hash_to_records = defaultdict(list)

    print(f"Processing PlasticDB file: {plasticdb_file}")
    record_count = 0
    duplicate_count = 0
    start_time = time.time()

    for record in SeqIO.parse(plasticdb_file, "fasta"):
        record_count += 1
        if record_count % 10000 == 0:
            elapsed = time.time() - start_time
            print(
                f"Processed {record_count} PlasticDB sequences... ({record_count/elapsed:.2f} seqs/sec)"
            )

        seq_id = record.id
        description = record.description
        sequence = str(record.seq).upper()

        # Use MD5 hash of sequence as key for memory efficiency
        seq_hash = hashlib.md5(sequence.encode()).hexdigest()

        # If no_duplicates is True and we already have this sequence, skip it
        if no_duplicates and seq_hash in seq_hash_to_records:
            duplicate_count += 1
            continue

        if verify_exact:
            seq_hash_to_records[seq_hash].append(
                (seq_id, description, len(sequence), sequence)
            )
        else:
            seq_hash_to_records[seq_hash].append((seq_id, description, len(sequence)))

    elapsed = time.time() - start_time
    print(
        f"Completed processing {record_count} PlasticDB sequences in {elapsed:.2f} seconds"
    )
    print(f"Number of unique sequence hashes: {len(seq_hash_to_records)}")
    if no_duplicates:
        print(f"Removed {duplicate_count} duplicate sequences")

    return seq_hash_to_records


def find_matches_in_pazy(plasticdb_lookup, pazy_file, output_file, verify_exact=False):
    """
    Find PAZy sequences that match with PlasticDB sequences and write to output TSV.
    """
    with open(output_file, "w") as out_f:
        # Write header
        out_f.write(
            "PAZy_ID\tPAZy_Description\tPlasticDB_ID\tPlasticDB_Description\tSequence_Length\n"
        )

        print(f"Processing PAZy file: {pazy_file}")
        record_count = 0
        match_count = 0
        start_time = time.time()

        for record in SeqIO.parse(pazy_file, "fasta"):
            record_count += 1
            if record_count % 1000 == 0:
                elapsed = time.time() - start_time
                print(
                    f"Processed {record_count} PAZy sequences, found {match_count} matches... ({record_count/elapsed:.2f} seqs/sec)"
                )

            pazy_id = record.id
            pazy_description = record.description
            pazy_seq = str(record.seq).upper()

            seq_hash = hashlib.md5(pazy_seq.encode()).hexdigest()

            if seq_hash in plasticdb_lookup:
                for plasticdb_record in plasticdb_lookup[seq_hash]:
                    if verify_exact:
                        plasticdb_id, plasticdb_desc, seq_len, plasticdb_seq = (
                            plasticdb_record
                        )
                        # Verify exact sequence match
                        if pazy_seq != plasticdb_seq:
                            continue  # Skip if sequences don't match exactly
                    else:
                        plasticdb_id, plasticdb_desc, seq_len = plasticdb_record

                    out_f.write(
                        f"{pazy_id}\t{pazy_description}\t{plasticdb_id}\t{plasticdb_desc}\t{seq_len}\n"
                    )
                    match_count += 1

    elapsed = time.time() - start_time
    print(
        f"Completed processing {record_count} PAZy sequences in {elapsed:.2f} seconds"
    )
    print(f"Found {match_count} matches")
    return match_count


def main():
    parser = argparse.ArgumentParser(
        description="Find matching sequences between PlasticDB and PAZy databases"
    )
    parser.add_argument(
        "--plasticdb", required=True, help="Path to PlasticDB FASTA file"
    )
    parser.add_argument("--pazy", required=True, help="Path to PAZy FASTA file")
    parser.add_argument("--output", required=True, help="Path to output TSV file")
    parser.add_argument(
        "--verify-exact",
        action="store_true",
        help="Verify exact sequence matches (more memory intensive)",
    )
    parser.add_argument(
        "--noduplicates",
        action="store_true",
        help="Remove duplicate sequences from PlasticDB (keeps only first occurrence)",
    )
    args = parser.parse_args()

    # Create lookup from PlasticDB
    plasticdb_lookup = create_plasticdb_lookup(
        args.plasticdb, args.verify_exact, args.noduplicates
    )

    # Find matches in PAZy
    match_count = find_matches_in_pazy(
        plasticdb_lookup, args.pazy, args.output, args.verify_exact
    )

    print(f"{match_count} cross-references written to {args.output}")


if __name__ == "__main__":
    main()
