#! /usr/bin/python3
"""
Paste many elasticsearch aggregation buckets over same time period into one table
"""
__author__    = "Romain Loth"
__copyright__ = "Copyright 2016 ISCPIF-CNRS"
__license__   = "LGPL"
__version__   = "0.5"
__email__     = "romain.loth@iscpif.fr"
__status__    = "dev"

from argparse import ArgumentParser
from sys      import argv, stderr
from json     import load
from glob     import glob
from re       import search
from os       import path

DEFAULT_BUCKETS_JSON_DIR="/home/romain/tw/risk2015_scraps/recency/all_crawled"


FROM_YEAR = 2000
UPTO_YEAR = 2015

all_years = [y for y in range(FROM_YEAR, UPTO_YEAR+1)]

# range +1 last value
# exemple: range(2000,2016)
# [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015]


if __name__ == '__main__':
    # cli args
    # --------
    parser = ArgumentParser(
        description="Paste many elasticsearch aggregation buckets (JSON) over a constant time period into one table on an external list of terms...",
        epilog="-----(© 2016 ISCPIF-CNRS romain.loth at iscpif dot fr )-----")

    parser.add_argument('-d',
        metavar='pathto/jsondir',
        help='the dir with the json time buckets for each term',
        default=DEFAULT_BUCKETS_JSON_DIR,
        required=True,
        action='store')

    args = parser.parse_args(argv[1:])

    buckets_paths = glob(args.d+"/*.json")
    if not len(buckets_paths):
        print("no files matching '*.json' were found under in directory '%s'"
                % args.d,
                file=stderr)
        exit(1)
    else:
        # print("debug: just 3:", buckets_paths[0:3])
        for bucket_path in buckets_paths:
            term_id = search(r'^\d+',path.basename(bucket_path)).group()

            output_vals = {} # year by year dict
            output_line = term_id

            # try:

            fh = open(bucket_path, "r")
            # json.load to read the data
            all_json = load(fh)
            fh.close()

            # todo match in path
            term_id = search("r'^\d+", bucket_path)

            bucket_info = all_json['aggs']['publicationCount']['buckets']
            # print(bucket_info)

            # secondary loop to test for missing years :(
            for year in all_years:
                found = False
                for i, bk in enumerate(bucket_info):
                    if int(bk['key']) == year:
                        found = i
                        break
                if found:
                    output_vals[year] = bucket_info[found]['doc_count']
                else:
                    output_vals[year] = 0
            # except Exception as e:
            #     print("WARNING: term_id", term_id, "has error:", str(e) )
            #     for year in all_years:
            #         output_vals[year] = -1

            # now the csv line
            for year in all_years:
                output_line += "\t"+ str(output_vals[year])

            print(output_line)
