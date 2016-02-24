#! /usr/bin/python3
"""
Filters an ES terms aggregation (JSON) on an external list of terms

The filtering master list can be retrieved from a directory of gexf files or provided as a one per line txt doc.

TODO aggregate k weeks in a time bucket
"""
__author__    = "Romain Loth"
__copyright__ = "Copyright 2016 ISCPIF-CNRS"
__license__   = "LGPL"
__version__   = "0.5"
__email__     = "romain.loth@iscpif.fr"
__status__    = "dev"


from argparse import ArgumentParser
from sys      import argv, stderr
from json     import load, dumps
from glob     import glob
from lxml     import etree

DEFAULT_MASTER_GEXF_DIR="/var/www/COP21/data/ClimateChange"
DEFAULT_INPUT_JSON_PATH="Climate_Change_Weekly_new.json"

def retrieve_gexf_node_labels(my_path):
    "mypath points to a gexf XML file"

    # parse gexf
    try:
        gexfdom = etree.parse(my_path)
    except etree.XMLSyntaxError as e:
        print("gexf xml input error: %s %s (skip)" 
                    % (my_path, e),
                    file=stderr)
        return []

    # xpath
    my_xpath_elts = ['gexf','graph','nodes','node']
    nsfree_path = "".join(
                ["/*[local-name()=\"%s\"]" % elt for elt in my_xpath_elts]
            )
    all_labels = gexfdom.xpath(nsfree_path+'/@label')
    
    # print(nsfree_path+'/@label', file=stderr)

    return all_labels

def read_master_list(my_path):
    "one term per line"
    terms_array = []
    f = open(my_path, 'r')
    for line in f:
        term = line.rstrip('\n')
        if len(term):
            terms_array.append(term)
    f.close()
    return terms_array

def add_list_to_dict(a_list, previous_dict = {}):
    "list => dict keys"
    for term in a_list:
        previous_dict[term] = True
    return previous_dict

class TimeBucket:
    "Contains the same properties as an ES timeline bucket object"
    def __init__(self, key_as_string, key):
        self.kas = key_as_string
        self.k   = key
        
        # updated doc count to increment
        self.dc  = 0
        
        # for keyword buckets
        self.kws = []
    
    def as_dict(self):
        "dict for json serialization"
        return {
            "key_as_string" : self.kas,
            "key"           : self.k,
            "doc_count"     : self.dc,
            "keywords" : {
                "buckets" : self.kws
            }
        }


if __name__ == '__main__':
    # cli args
    # --------
    parser = ArgumentParser(
        description="Filters an ES terms aggregation (JSON) on an external list of terms... The filtering master list can be retrieved from a directory of gexf files (keeping only the terms that correspond to a gexf node label) or provided as a one per line txt doc.",
        epilog="-----(© 2016 ISCPIF-CNRS romain.loth at iscpif dot fr )-----")
    
    parser.add_argument('-i',
        metavar='pathto/input.json',
        help='path to a JSON with ES-style time + terms aggregations',
        default=DEFAULT_INPUT_JSON_PATH,
        required=False,
        action='store')

    parser.add_argument('-d',
        metavar='pathto/gexfdir',
        help='the dir with the gexf with the target terms (ie their //node/@label)',
        default=DEFAULT_MASTER_GEXF_DIR,
        required=False,
        action='store')

    parser.add_argument('-l',
        metavar='pathto/termlist',
        help='alternative to -d : a path with a prepared master term list (a txt file with one term per line)',
        default=None,
        required=False,
        action='store')
   
    args = parser.parse_args(argv[1:])


    # MAIN
    # ----

    # 1) the dict of terms to keep
    filter_dict = {}

    if args.l:
        filter_dict = read_master_list(args.l)
    else:
        gexf_paths = glob(args.d+"/*.gexf")
        if not len(gexf_paths):
            print("no files matching '*.gexf' were found under in directory '%s'" 
                    % args.d, 
                    file=stderr)
            exit(1)
        else:
            for gexf_path in gexf_paths:
                # grep our labels in the xml
                node_labels = retrieve_gexf_node_labels(gexf_path)
                
                # fyi
                n = len(node_labels)
                
                # update our dict
                filter_dict = add_list_to_dict(node_labels, filter_dict)
                
                print("found %i labels in gexf file '%s'"
                        % (n, gexf_path),
                        file = stderr
                    )

    print('master filter list has a total of %i unique terms' 
            % len(filter_dict),
            file=stderr
          )

    # 2) loop the input json
    aggs_f = open(args.i, 'r')

    aggs_json = load(aggs_f)

    # result: same json (as dict) but filtered
    filtered = {
        'hits': aggs_json['hits'],     # we keep the same property hits
        'aggregations' : {             # and an empty aggs structure
            'weekly' : {
                'buckets' : []
            }
        }
    }

    print("filtering input json '%s'" % args.i, file = stderr)

    # counters
    count = {'t_buckets': 0, 'kw_buckets_in': 0, 'kw_buckets_out': 0 }

    for time_bucket in aggs_json['aggregations']['weekly']['buckets']:
        count['t_buckets'] += 1

        # initialize our copy
        tb_copy = TimeBucket(
                time_bucket['key_as_string'],
                time_bucket['key']
            )

        # now the keywords
        for kw in time_bucket['keywords']['buckets']:
            count['kw_buckets_in'] += 1
            
            # print(kw)
            this_term = kw['key']
            
            # the filtering ------------
            if this_term in filter_dict:
                # the keeping
                this_count = kw['doc_count']
                tb_copy.kws.append( 
                    {
                        'key': this_term,
                        'doc_count': this_count
                    }
                )
                # we add to new total
                tb_copy.dc += this_count

                # and keep track
                count['kw_buckets_out'] += 1

        # save the time bucket
        filtered['aggregations']['weekly']['buckets'].append(
            tb_copy.as_dict()
        )
    
    aggs_f.close()

    # fyi
    print ('kept %i/%i "keyword buckets" across %i "time buckets"'
            % (
                count['kw_buckets_out'],
                count['kw_buckets_in'],
                count['t_buckets']
            ),
            file = stderr
        )

    # 3) output on STDOUT
    print("writing output json to STDOUT", file = stderr)
    print(dumps(filtered, indent=1))
