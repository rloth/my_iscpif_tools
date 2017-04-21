#! /usr/bin/python3
"""
Read a gexf and query each node label with an API to create a new node attribute (ex: growth_rate) in the gexf
"""
__author__    = "Romain Loth"
__copyright__ = "Copyright 2017 ISCPIF-CNRS"
__license__   = "LGPL"
__version__   = "1"
__email__     = "romain.loth@iscpif.fr"
__status__    = "dev"

from argparse  import ArgumentParser
from sys       import argv, stderr
from lxml      import etree
from re        import sub, search
from os        import path
from requests  import get
from time      import sleep

DEFAULT_API_URL = "https://api.iscpif.fr/v2/pub/politic/france/twitter/histogram"
DEFAULT_API_INTERVAL = "day"
DEFAULT_ATTRIBUTE = "growth_rate"

PARAM_MAX_RETRIES = 5

PARAM_AGE_THRESHOLD = 10

# prepare corresponding namespace
MY_NS = {"g":"http://www.gexf.net/1.3"}

def get_values(tableName):
    # read input table
    vals_per_id = {}
    table_fh = open(tableName, 'r')
    for i, line in enumerate(table_fh):
        line = line.rstrip()
        try:
            (nodeid, value) = line.split("\t")
            # print(nodeid, value)
            vals_per_id[str(nodeid)] = float(value)
        except:
            print('WARN skip tsv line %i ("%s")' % (i, line), file=stderr)
    table_fh.close()

    # debug print whole dict
    # print(vals_per_id)

def add_attr_declaration(xml_tree, attr_name, format = 'float'):
    """
    for output       NB assumes there already is an <attributes> element
    (modifies the tree in-place)
    """
    attrs_declaration = xml_tree.xpath(
        '/g:gexf/g:graph/g:attributes[@class="node"]',
        namespaces=MY_NS).pop()
    new_attr_declaration = etree.Element("attribute")
    new_attr_declaration.attrib['id']    = attr_name
    new_attr_declaration.attrib['title'] = attr_name
    new_attr_declaration.attrib['type']  = format
    attrs_declaration.append(new_attr_declaration)


def insert_attribute(xml_node, attr_name, attr_val):
    """
    for output
    (modifies the node in-place)
    insert into one gexf:node
    """
    current_attrs = xml_node.xpath('g:attvalues', namespaces=MY_NS).pop()

    # the fragment to add
    # -------------------
    # ex: <attvalue for="bidule" value="5.32">
    new_attr = etree.Element("attvalue")
    new_attr.attrib['for'] = attr_name
    new_attr.attrib['value'] = str(attr_val)

    # add in this node
    current_attrs.append(new_attr)



##### time-aggregation transforms  (buckets => value) #####
def transform_growth_rate(label_counts, timescale):

    result = {'format': 'float', 'node_vals':{}}

    infinity = 1000

    n_ticks = len(timescale)
    mid = int(n_ticks/2)
    first_half = timescale[:mid]
    second_half = timescale[mid:]

    # print("first_half", first_half, file=stderr)
    # print("second_half", second_half, file=stderr)

    for label in label_counts:
        first_sum = 0
        second_sum = 0

        for timebucket in first_half:
            if timebucket in all_counts[label]:
                val = all_counts[label][timebucket]
                first_sum += val

        for timebucket in second_half:
            if timebucket in all_counts[label]:
                val = all_counts[label][timebucket]
                second_sum += val


        if first_sum > 0:
            result['node_vals'][label] = "%.3f" % (second_sum / first_sum)
        elif second_sum > 0:
            result['node_vals'][label] = infinity
        else:
            result['node_vals'][label] = -1

    return result


def transform_age(label_counts, timescale):
    """
    for each label, returns first date where label_count > 0
    """

    # value will be epoch key
    result = {'format': 'int', 'node_vals':{}}

    for label in label_counts:
        apparition_time = 0

        for timebucket in timescale:
            if timebucket in all_counts[label]:
                if all_counts[label][timebucket] > PARAM_AGE_THRESHOLD:
                    # we use timebuckets_census to retrieve also epoch keys
                    apparition_time = timebuckets_census[timebucket]
                    break

        result['node_vals'][label] = apparition_time

    return result



# attr_name => bucket ags
AVAILABLE_FUNCTIONS = {
    "growth_rate": transform_growth_rate,
    "age": transform_age,
}


if __name__ == '__main__':

    # future list of all encountered buckets for normalize
    timebuckets_census = {}
    timebuckets_scale = []   # sorted keys of the previous

    # mask values dict {bucket_key: val for q='*'}
    total_counts = {}

    # values dict { query_expression:{bucket_key: val}}
    all_counts = {}

    # cli args
    # --------
    parser = ArgumentParser(
        description="Read a gexf and query each node label with an API to create a new node attribute (ex: growth_rate) in the gexf",
        epilog="-----(© 2017 ISCPIF-CNRS romain.loth at iscpif dot fr )-----")

    parser.add_argument('--gexf',
        metavar='pathto/graph.gexf',
        help='input graph',
        required=True,
        action='store')

    parser.add_argument('--url',
        default=DEFAULT_API_URL,
        metavar='https://someapi.iscpif.fr/histogram',
        help='URL of the remote API accepting q="somelabel"',
        required=False,
        action='store')

    # NB this triggers an associated function from AVAILABLE_FUNCTIONS
    parser.add_argument('--attr',
        metavar='new_attribute_tagname',
        help='name for the new attribute (possible choices: growth_rate, age)',
        default=DEFAULT_ATTRIBUTE,
        required=False,
        action='store')

    parser.add_argument('--apiSince',
        metavar='2017-01-01',
        help='since param for the api',
        required=False,
        action='store')

    parser.add_argument('--apiUntil',
        metavar='2017-04-01',
        help='until param for the api',
        required=False,
        action='store')

    parser.add_argument('--apiInterval',
        metavar='days',
        default=DEFAULT_API_INTERVAL,
        help='interval param for the api (day, week, month, year)',
        required=False,
        action='store')

    parser.add_argument('--verbose',
        default=False,
        help='more runtime logs',
        required=False,
        action='store_true')

    # parser.add_argument('--normalize',
    #     default=False,
    #     type = bool,
    #     help='divide by the total counts',
    #     required=False,
    #     action='store')

    args = parser.parse_args(argv[1:])

    if args.attr:
        # normalize name of the new attribute
        new_attr_name = sub(r'\W+', '_', args.attr)
        new_attr_name = sub(r'^_+', '', new_attr_name)
        new_attr_name = sub(r'_+$', '', new_attr_name)

    # read input xml graph
    xml_tree = etree.parse(args.gexf)

    print("==READ xml tree: finished==", file=stderr)

    # get all nodes by xpath
    nodes = xml_tree.xpath('/g:gexf/g:graph/g:nodes/g:node', namespaces=MY_NS)

    api_args = {"interval":args.apiInterval }

    if args.apiSince:
        api_args['since'] = args.apiSince
    if args.apiUntil:
        api_args['until'] = args.apiUntil

    print('api_args', api_args, file=stderr)

    # READ
    for node in nodes:
        expression = node.attrib['label']

        if len(expression):

            result_buckets = None

            if args.verbose:
                print('===== expression:"%s" =====' % expression, file=stderr)

            # REMOTE QUERY
            api_args['q'] = expression
            resp = get(args.url, params=api_args)

            if args.verbose:
                print('queryied url:', resp.url, file=stderr)

            try:
                result_buckets = resp.json()
                # ex:
                # {'results': {'hits': [
                #    {'doc_count': 1,
                #     'key': 1420070400000,
                #     'key_as_string': '2015-01-01T00:00:00.000Z'},
                #    {'doc_count': 7488103,
                #     'key': 1451606400000,
                #     'key_as_string': '2016-01-01T00:00:00.000Z'},
                #    {'doc_count': 13049936,
                #     'key': 1483228800000,
                #     'key_as_string': '2017-01-01T00:00:00.000Z'}
                #  ],
                # 'took': 506,
                # 'total': 20538040}}
            except:
                nretries = 0
                while result_buckets is None and nretries < PARAM_MAX_RETRIES:
                    # wait two seconds and retry
                    sleep(2)
                    nretries += 1
                    print("retrying %i query for '%s'" % (nretries, expression), file=stderr)
                    try:
                        resp = get(args.url, params=api_args)
                        result_buckets = resp.json()
                    except:
                        pass
                if result_buckets is None:
                    print("GIVING UP query for '%s'" % expression, file=stderr)
                    result_buckets = {'hits': []}



            for hit in result_buckets['results']['hits']:

                if args.verbose:
                    print("hit", hit, file=stderr)
                bucket_key = hit['key_as_string']

                # global census
                timebuckets_census[bucket_key] = hit['key']

                # per-word counts
                if expression not in all_counts:
                    all_counts[expression] = {}
                all_counts[expression][bucket_key] = hit["doc_count"]

    # print(all_counts, file=stderr)

    timebuckets_scale = sorted([k for k in timebuckets_census])

    # print("sorted entries in timebucket", "\n".join(timebuckets_scale), file=stderr)



    # apply a transformation (all_counts, scale) => one value per label

    my_bucket_aggregation = AVAILABLE_FUNCTIONS[new_attr_name]

    # results = transform_growth_rate(all_counts, timebuckets_scale)
    results = my_bucket_aggregation(all_counts, timebuckets_scale)


    # WRITE OUTPUT
    # 1 - add once the attribute declaration
    add_attr_declaration(xml_tree, new_attr_name, results['format'])

    # 2 - insert computed value in each nodes' xml
    for node in nodes:
        this_node_label = node.attrib['label']

        if this_node_label in results['node_vals'] and results['node_vals'][this_node_label] is not None:
            node = insert_attribute(
                    node, new_attr_name,
                    results['node_vals'][this_node_label])
        # else:
        #     print("no value for node %s" % this_node_label, file=stderr)

    # print resulting XML to STDOUT
    print(etree.tostring(xml_tree, pretty_print=True).decode('UTF-8'))
