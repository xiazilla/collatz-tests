#!/usr/bin/python

import os
import errno
import re
import subprocess
import sys

CURRENT_DIRECTORY = os.getcwd()
OVERFLOW_INPUTS_FILE = "{cwd}/overflow_inputs.txt".format(cwd=CURRENT_DIRECTORY)
OVERFLOW_INPUTS = []
VERBOSE = len(sys.argv) >= 2 and sys.argv[1] == '-v'
RUN_TESTS = len(sys.argv) >= 2 and sys.argv[1] == '-r'

found_invalid_file = False

def is_valid_file(filename):
    is_in_file = filename.endswith('.in')
    is_run_collatz = filename[filename.find('-')+1:-3] == 'RunCollatz'

    return is_in_file and is_run_collatz

with open(OVERFLOW_INPUTS_FILE, "r") as f:
    numbers = [int(line) for line in f.readlines()]
    OVERFLOW_INPUTS = numbers

for filename in (f[0:-3] for f in filter(is_valid_file, os.listdir(CURRENT_DIRECTORY))):
    full_filename_builder = "{test_dir}/{filename}{ext}"
    in_filename = full_filename_builder.format(test_dir=CURRENT_DIRECTORY, filename=filename, ext='.in')
    test_is_invalid = False

    # Verify that tests don't contain invalid numbers
    with open(in_filename, 'r') as in_file:
        # Ignore lines that don't match predicted input
        for lineno, line in enumerate(l for l in in_file.readlines() if re.match("\d+\s\d+", l)):
            if not re.match("\d+\s\d+", line):
                if line == "":
                    continue
                else:
                    print ("{f}.in:{l}: Invalid line contents \"{c}\"".format(f=filename, l=lineno, c=line))
                    continue
            i, j = map(lambda x: int(x), line.split(' '))

            # Need to swap for algorithm to work
            if i > j:
                temp = i
                i = j
                j = temp

            # Test is invalid if any number in the range [i, j] causes overflow of 32bit integers
            if any((num >= i and num <= j for num in OVERFLOW_INPUTS)):
                if RUN_TESTS:
                    print ("{f}.in: Contains invalid range, will skip testing".format(f=filename))
                elif VERBOSE:
                    overflow_candidates = [num for num in OVERFLOW_INPUTS if num >= i and num <= j]
                    for candidate in overflow_candidates:
                        print ("{f}.in:{l}: Range {i}-{j} contains overflow number {o}".format(
                            f=filename,
                            l=lineno,
                            i=i,
                            j=j,
                            o=candidate))
                else:
                    print ("{f}.in:{l}: Invalid range {i}-{j}".format(
                        f=filename,
                        l=lineno,
                        i=i,
                        j=j,
                    ))
                if RUN_TESTS:
                    test_is_invalid = True
                else:
                    found_invalid_file = True
                break
    
    # If asked to, run the test.
    if RUN_TESTS:
        try:
            os.remove("{f}.tmp")
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        p = subprocess.Popen("../RunCollatz < {f}.in > {f}.tmp && diff {f}.tmp {f}.out".format(f=filename), 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            print("{f}.in: exited with status {c}".format(f=filename, c=p.returncode))
            found_invalid_file = True

if found_invalid_file:
    sys.exit(1)
