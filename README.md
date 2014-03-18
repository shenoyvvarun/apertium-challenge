Coding Challenge for Apertium project: Command-line translation memory fuzzy-match repair

To Use the tool:

<program>.py -c from-to -s source_sentence -t target_sentence -d apertium_directory [-r]

The tool, takes the target and source setences using the output of morphological analyser and once we have the contractions expanded. Finds all pairs, translates all of them in a single shot using the apertium process and tries to find these translation in the translated sentence.
