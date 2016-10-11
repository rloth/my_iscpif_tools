#! /usr/bin/python3
"""
Read a [nodeid - val] tsv table
and introduce the val as a node
attribute in a gexf
"""
__author__    = "Romain Loth"
__copyright__ = "Copyright 2016 ISCPIF-CNRS"
__license__   = "LGPL"
__version__   = "0.5"
__email__     = "romain.loth@iscpif.fr"
__status__    = "dev"

from argparse import ArgumentParser
from sys      import argv, stderr
from lxml     import etree
from re       import sub

if __name__ == '__main__':
    # cli args
    # --------
    parser = ArgumentParser(
        description="Read a [nodeid - val] tsv table and introduce the val as a node attribute in a gexf",
        epilog="-----(© 2016 ISCPIF-CNRS romain.loth at iscpif dot fr )-----")

    parser.add_argument('-t',
        metavar='pathto/table.tsv',
        help='input table, with 2 columns: nodeid value',
        # default=DEFAULT_BUCKETS_JSON_DIR,
        required=True,
        action='store')

    parser.add_argument('-n',
        metavar='new_attribute_tagname',
        help='name for the new attribute',
        # default=DEFAULT_BUCKETS_JSON_DIR,
        required=True,
        action='store')

    parser.add_argument('-g',
        metavar='pathto/graph.gexf',
        help='input graph, with same nodeids as in the table',
        required=False,
        action='store')

    args = parser.parse_args(argv[1:])

    # normalize name of the new attribute
    new_attr_name = sub(r'\W+', '_', args.n)
    new_attr_name = sub(r'^_+', '', new_attr_name)
    new_attr_name = sub(r'_+$', '', new_attr_name)

    # read input table
    vals_per_id = {}
    table_fh = open(args.t, 'r')
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

    # read input xml graph
    xml_tree = etree.parse(args.g)

    # prepare corresponding namespace
    my_ns = {"g":"http://www.gexf.net/1.3"}

    # add once the attribute declaration
    attrs_declaration = xml_tree.xpath('/g:gexf/g:graph/g:attributes[@class="node"]', namespaces=my_ns).pop()
    new_attr_declaration = etree.Element("attribute")
    new_attr_declaration.attrib['id']    = new_attr_name
    new_attr_declaration.attrib['title'] = new_attr_name
    new_attr_declaration.attrib['type']  = "float"
    attrs_declaration.append(new_attr_declaration)

    # get all nodes by xpath
    nodes = xml_tree.xpath('/g:gexf/g:graph/g:nodes/g:node', namespaces=my_ns)

    # insert value in each nodes' xml
    for node in nodes:
        this_node_id = node.attrib['id']
        current_attrs = node.xpath('g:attvalues', namespaces=my_ns).pop()

        # the fragment to add
        # -------------------
        # ex: <attvalue for="bidule" value="5.32">
        new_attr = etree.Element("attvalue")
        new_attr.attrib['for'] = new_attr_name
        new_attr.attrib['value'] = str(vals_per_id[this_node_id])

        # add in this node
        current_attrs.append(new_attr)


    # print resulting XML to STDOUT
    print(etree.tostring(xml_tree, pretty_print=True).decode('UTF-8'))
