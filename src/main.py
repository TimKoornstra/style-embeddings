#!/usr/bin/env python3

# > Imports
# Standard Library
import argparse
import os
import pickle
from random import sample

# Local
from data import pipeline, load_data
from pairings import split_data, create_pairings


def add_arguments(parser):
    """
    Add the arguments to the parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to add the arguments to.

    """
    parser.add_argument("--data_source", type=str, default="reddit",
                        help="The data source to use for the model.\
                                (default: reddit)")
    parser.add_argument("-p", "--path", type=str, default="",
                        help="The path to the pre-processed data \
                                pickle file. (default: '')")
    parser.add_argument("--cache_path", type=str, default=".cache/",
                        help="The path to the cache directory. All temporary\
                                models and data will be saved here.\
                                (default: '.cache/')")
    parser.add_argument("--output_path", type=str, default="output/",
                        help="The path to the output directory.\
                                (default: 'output/')")


if __name__ == '__main__':
    # Parse the input arguments
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    # If the file exists, load the data from the file
    if os.path.exists(args.path):
        if args.path.endswith(".pkl"):
            print("Loading data locally...")
            df = load_data(args.path)
            print("Data loaded.")
        else:
            raise ValueError(f"Invalid pickle file: {args.path}")
    else:
        # Run the preprocessing pipeline
        df = pipeline(data_source=args.data_source,
                      output_path=args.output_path,
                      cache_path=args.cache_path)

    # Split the data into train, validation, and test sets
    train, val, test = split_data(df[:500000])

    # Check that the author_id's are non-overlapping
    assert len(set(train["author_id"]).intersection(
        set(val["author_id"]))) == 0

    # Create the pairings
    print("Creating pairings...")
    train_pairings, s_pairings = create_pairings(
        train,
        semantic_range=(0.7, 1.0),
        max_negative=3,
        output_path=args.output_path,
        paraphrase_path=f"{args.output_path}/data/paraphrases_{len(train)}.pkl")
    print("Pairings created.")

    print("=============================")
    print("Semantically similar examples")
    print("=============================")
    for example in sample(s_pairings, 10):
        print(f"{example[0]}")
        print("\n---\n")
        print(f"{example[1]}")
        print("\n=============================\n")

    # Count the number of positive and negative examples
    n_positive = sum([1 for _, _, label in train_pairings if label == 1])
    n_negative = sum([1 for _, _, label in train_pairings if label == 0])

    print(f"Number of positive examples: {n_positive}")
    print(f"Number of negative examples: {n_negative}")

    # Save the pairings to a pickle file
    with open(f"{args.output_path}/data/train_pairings.pkl", "wb") as f:
        pickle.dump(train_pairings, f)

    with open(f"{args.output_path}/data/s_pairings.pkl", "wb") as f:
        pickle.dump(s_pairings, f)
