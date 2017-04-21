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

# prepare corresponding namespace
MY_NS = {"g":"http://www.gexf.net/1.3"}

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


if __name__ == '__main__':

    # values to copy, by node id
    copied_vals = {}

    # declared format ('int', etc)
    copied_format = None

    # cli args
    # --------
    parser = ArgumentParser(
        description="Read a gexf and query each node label with an API to create a new node attribute (ex: growth_rate) in the gexf",
        epilog="-----(© 2017 ISCPIF-CNRS romain.loth at iscpif dot fr )-----")

    parser.add_argument('--gexfsrc',
        metavar='pathto/graph.gexf',
        help='graph from which we read the values',
        required=True,
        action='store')

    parser.add_argument('--gexftgt',
        metavar='pathto/graph2.gexf',
        help='graph into which we merge the values and send, modified, to STDOUT',
        required=True,
        action='store')

    parser.add_argument('--attr',
        metavar='attr_name',
        help='name of the attribute to copy',
        required=True,
        action='store')

    args = parser.parse_args(argv[1:])

    if args.attr:
        # normalize name of the new attribute
        new_attr_name = sub(r'\W+', '_', args.attr)
        new_attr_name = sub(r'^_+', '', new_attr_name)
        new_attr_name = sub(r'_+$', '', new_attr_name)

    # read input xml graph
    xml_src_tree = etree.parse(args.gexfsrc)

    # get all source nodes by xpath
    source_nodes = xml_src_tree.xpath('/g:gexf/g:graph/g:nodes/g:node', namespaces=MY_NS)

    # store the declared format
    try:
        copied_format = xml_src_tree.xpath('/g:gexf/g:graph/g:attributes[@class="node"]/g:attribute[@title="%s"]/@type' % new_attr_name, namespaces=MY_NS).pop()
    except:
        copied_format = 'string'

    # READ graph 1 "src"
    for node in source_nodes:
        if ('id' in node.attrib):
            current_attr_elts = node.xpath('g:attvalues/g:attvalue[@for="%s"]' % new_attr_name, namespaces=MY_NS)
            if len(current_attr_elts) == 1:
                the_value = current_attr_elts[0].attrib['value']

                # store it
                copied_vals[node.attrib['id']] = the_value


    # ---------------------------------
    # now, let's modify all target nodes

    # read target xml graph
    xml_tgt_tree = etree.parse(args.gexftgt)

    # WRITE OUTPUT
    # 1 - add once the attribute declaration
    add_attr_declaration(xml_tgt_tree, new_attr_name, copied_format)

    # 2 - insert computed value in each nodes' xml
    target_nodes = xml_tgt_tree.xpath('/g:gexf/g:graph/g:nodes/g:node', namespaces=MY_NS)

    stat_n_missing_ids = 0
    for node in target_nodes:
        if ('id' in node.attrib):
            if (node.attrib['id'] in copied_vals):
                the_stored_value = copied_vals[node.attrib['id']]
                insert_attribute(node, new_attr_name, the_stored_value)
            else:
                stat_n_missing_ids += 1

    print('Missing ids: %i' % stat_n_missing_ids, file=stderr)

    # print resulting XML to STDOUT
    print(etree.tostring(xml_tgt_tree, pretty_print=True).decode('UTF-8'))
