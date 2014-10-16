#!/usr/bin/env python
"""Utilities for documentation.

See Also
--------
RELATED : {}

Notes
-----
Docstring formats adapted from [1]_.
TODO : To-do items are flagged with 'TODO:'.
See Also : Sets of related objects, categorized by `CALLS`, `CALLED_BY`, `RELATED`.

References
----------
.. [1] https://github.com/numpy/numpy/blob/master/doc/example.py

"""
# TODO: use http://sphinx-doc.org/


# Import standard libraries.
from __future__ import absolute_import, division, print_function
import ast
import sys
import pdb
# Import external packages.
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
# Import internal modules.


def parse_see_also(line):
    """Parse field from 'See Also' section of docstring.
    
    Parameters
    ----------
    line : string
        Example 1: '    CALLS : {}'
        Example 2: '    CALLED_BY : {func1}'
        Example 3: '    RELATED : {func1, func2}'
    
    Returns
    -------
    field : set
        {''} returned as empty set instead of {} to allow iteration through the set
        Example 1: {''}
        Example 2: {'func1'}
        Example 3: {'func1', 'func2'}
    
    See Also
    --------
    CALLS : {}
    CALLED_BY : {parse_docstring}
    RELATED : {}
    
    Notes
    -----
    Docstring format adapted from [1]_.
    
    References
    ----------
    .. [1] https://github.com/numpy/numpy/blob/master/doc/example.py
    
    """
    field = line.split(':')[1].strip()
    field = [elt.strip().replace('`', '').replace('\'', '').replace('"', '') for elt in field.split(',')]
    field = [elt.replace('{', '').replace('}', '') for elt in field]
    return set(field)


def parse_docstring(docstring):
    """Parse relationships from docstring.
    
     Returns a generator that iterates through (field, value) tuples.
     Docstring must have 'See Also' section with the fields 'CALLS', 'CALLED_BY', 'RELATED'.

    Parameters
    ----------
    docstring : string
        Line separators are '\n'.

    Returns
    -------
    field : string
        Examples: 'CALLS', 'CALLED_BY', 'RELATED'
    value : set
        Examples: {''}, {'func1', 'func2'} 
    
    See Also
    --------
    CALLS : {parse_see_also}
    CALLED_BY : {}
    RELATED : {}
    
    Notes
    -----
    Docstring format adapted from [1]_.
    
    References
    ----------
    .. [1] https://github.com/numpy/numpy/blob/master/doc/example.py

    """
    lines = docstring.split('\n')
    catch_calls = None
    catch_called_by = None
    catch_related = None
    for line in lines:
        if 'See Also' in line:
            catch_calls = True
            catch_called_by = True
            catch_related = True
            continue
        elif catch_calls and 'CALLS' in line:
            catch_calls = False
            yield ('CALLS', parse_see_also(line))
            continue
        elif catch_called_by and 'CALLED_BY' in line:
            catch_called_by = False
            yield ('CALLED_BY', parse_see_also(line))
            continue
        elif catch_related and 'RELATED' in line:
            catch_related = False
            yield ('RELATED', parse_see_also(line))
            continue
        else:
            continue


def make_docs_dict(fpath):
    """Parse file to make dict of docstrings.
    
    Parameters
    ----------
    fpath : string
        Path to file.
        Example: '/path/to/module.py'
    
    Returns
    -------
    docs_dict : dict
        ``dict`` of parsed docstring.
        Includes attribute names from ``ast`` package:
        lineno : line number
        col_offset : column offset number
    
    See Also
    --------
    CALLS : {parse_docstring}
    CALLED_BY : {}
    RELATED : {}
    
    Notes
    -----
    Nested structure is not preserved.
    
    References
    ----------
    .. [1] http://greentreesnakes.readthedocs.org/en/latest/manipulating.html
    
    """
    # TODO: check if CALLS, CALLED_BY, RELATED are existing nodes.
    with open(fpath, 'rb') as fobj:
        tree = ast.parse(''.join(fobj))
    docs_dict = {'docstring': ast.get_docstring(tree)}
    for (field, value) in parse_docstring(docs_dict['docstring']):
        docs_dict[field] = value
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docs_dict[node.name] = {}
            docs_dict[node.name]['lineno'] = int(node.lineno)
            docs_dict[node.name]['col_offset'] = int(node.col_offset)
            docs_dict[node.name]['docstring'] = ast.get_docstring(node)
            for (field, value) in parse_docstring(docs_dict[node.name]['docstring']):
                docs_dict[node.name][field] = value
    return docs_dict


def pretty_print_dict(dobj, indent=0):
    """Recursively print dict with formatting.
    
    Parameters
    ----------
    dobj : dict
    indent : {0}, int, optional
        Top-level indent.
        
    Returns
    -------
    None
    
    See Also
    --------
    CALLS : {}
    CALLED_BY : {}
    RELATED : {make_docs_dict}
    
    """
    for key in sorted(dobj):
        if key == 'docstring':
            print(' '*indent+"{key}: [omitted]".format(key=key))
        else:
            if isinstance(dobj[key], dict):
                print(' '*indent+"{key}:".format(key=key))
                pretty_print_dict(dobj[key], indent=indent+2)
            else:
                print(' '*indent+"{key}: {val}".format(key=key, val=dobj[key]))
    return None


def generate_edges(dobj, parent=''):
    """Recursively yield edges of multi-direction graph from ``dict``.
    
    Parameters
    ----------
    dobj : dict
        Output from `make_docs_dict`.
    parent : {''}, string, optional
        Label for initial parent node.
        Use '' as place holder for null node so that node is hashable.
    
    Returns
    -------
    node1, node2 : hashable
        Hashable Python objects. '' used in place of ``None`` for null nodes.
    attr_dict : dict
        Example: {'relationship': 'CONTAINS'}
        
    See Also
    --------
    CALLS : {generate_edges}
    CALLED_BY : {make_graph}
    RELATED : {parse_see_also, make_docs_dict, generate_positions}
    
    """
    for key in sorted(dobj):
        if key == 'docstring':
            continue
        elif key in ['CALLS', 'CALLED_BY', 'RELATED']:
            node1 = parent
            node2s = dobj[key]
            for node2 in node2s:
                yield (node1, node2, {'relationship': key})
            continue
        elif isinstance(dobj[key], dict):
            node1 = parent
            node2 = key
            yield (node1, node2, {'relationship': 'CONTAINS'})
            for edge in generate_edges(dobj=dobj[key], parent=key):
                yield edge
            continue
        else:
            continue
        

def make_graph(dobj, parent=''):
    """Make graph from ``dict``.
    
    Parameters
    ----------
    dobj : dict
        Output from `make_docs_dict`.
    parent : {''}, string, optional
        Label for initial parent node.
        Use '' in place of ``None`` for empty nodes so that nodes are hashable.
    
    Returns
    -------
    graph : networkx.MultiDiGraph
    
    See Also
    --------
    CALLS : {generate_edges}
    CALLED_BY : {}
    RELATED : {make_docs_dict, plot_graph}

    """
    # TODO: make node attributes for lineno and col_offset
    graph = nx.MultiDiGraph()
    for (node1, node2, attr_dict) in generate_edges(dobj, parent=parent):
        graph.add_edge(node1, node2, attr_dict=attr_dict)
    # Remove empty node references.
    graph.remove_node('')
    return graph


def generate_positions(dobj, parent=''):
    """Recursively yield line and column number of nodes from ``dict``.
    
    Parameters
    ----------
    dobj : dict
        Output from `make_docs_dict`.
    parent : {''}, string, optional
        Label for initial parent node.
        Use '' as place holder for null node so that node is hashable.
    
    Returns
    -------
    node : hashable
        Hashable Python objects. '' used in place of ``None`` for null nodes.
    attr : string
        Attribute names from ``ast`` package:
        lineno : line number
        col_offset : column offset number
    value : int
        Value of attribute: line number, column offset number.
        
    See Also
    --------
    CALLS : {generate_positions}
    CALLED_BY : {make_positions_dict}
    RELATED : {make_docs_dict, generate_edges}
    
    """
    # TODO: make node attributes for lineno and col_offset
    for key in sorted(dobj):
        if key == 'lineno':
            node = parent
            yield (node, 'lineno', dobj[key])
            continue
        elif key == 'col_offset':
            node = parent
            yield (node, 'col_offset', dobj[key])
            continue
        elif isinstance(dobj[key], dict):
            for position in generate_positions(dobj=dobj[key], parent=key):
                yield position
                continue
        else:
            continue


def make_positions_dict(dobj, graph, parent=''):
    """Make positions from ``dict``.
    
    Parameters
    ----------
    dobj : dict
        Output from `make_docs_dict`.
    graph : networkx.MultiDiGraph
        Output from `make_graph`
    parent : {''}, string, optional
        Label for initial parent node.
        Use '' in place of ``None`` for empty nodes so that nodes are hashable.
    
    Returns
    -------
    positions : dict
        ``dict`` of ``list`` for use by ``networkx.draw``.
        Format:
        {node: [lineno, col_offset], ...}
    
    See Also
    --------
    CALLS : {generate_positions}
    CALLED_BY : {}
    RELATED : {make_docs_dict, plot_graph, make_graph}

    """
    # TODO: make node attributes for lineno and col_offset
    # TODO: space out nodes
    positions_df = pd.DataFrame(columns=['lineno', 'col_offset'])
    positions_df.index.names = ['node']
    for (node, attr, value) in generate_positions(dobj=dobj, parent=parent):
        if attr == 'lineno':
            positions_df.loc[node, 'lineno'] = int(value)
            continue
        elif attr == 'col_offset':
            positions_df.loc[node, 'col_offset'] = int(value)
            continue
        else:
            continue
    lineno_max = int(positions_df['lineno'].max(axis=0))
    nodes_only_in_graph = set(graph.nodes()) - set(positions_df.index.values)
    for node in nodes_only_in_graph:
        lineno_max += 1
        positions_df.loc[node, 'lineno'] = lineno_max
        positions_df.loc[node, 'col_offset'] = 0
    # Convert line numbers to relative positions. (0, 0) of plot is in lower left.
    # Convert dtype to use method='first' for rank.
    positions_df = positions_df.astype(float)
    positions_df.sort(columns=['lineno', 'col_offset'], axis=0, inplace=True)
    positions_df[['rankpct_lineno', 'rankpct_col_offset']] = \
        positions_df[['lineno', 'col_offset']].rank(axis=0, method='first', ascending=False, pct=True)
    positions_dict = positions_df.stack().unstack(['node']).to_dict()
    # Convert from dict of dict to dict of list. numpy order: [y, x]
    positions_dict = {node:[positions_dict[node]['rankpct_col_offset'],
                            positions_dict[node]['rankpct_lineno']] for node in sorted(positions_dict)}
    return positions_dict


def plot_graph(graph, fixed=None, positions=None, show_plot=True, fpath=None):
    """Plot graph.
    
    Parameters
    ----------
    graph : networkx.MultiDiGraph
        Output from `make_graph`
    fixed : {None}, list, optional
        Node around which to fix graph. Overrides `pos`.
        Example: fixed=['mod1']
    positions : {None}, dict, optional
        ``dict`` of ``list`` output from `make_positions_dict`.
        Requires `fixed` is ``None``, otherwise overridden. 
    show_plot : {True, False}, bool, optional
        Flag to display plot in window.
    fpath : {None}, string, optional
        Path for plotting graph.
    
    Returns
    -------
    None
    
    See Also
    --------
    CALLS : {}
    CALLED_BY : {}
    RELATED : {make_positions_dict, make_graph}

    """
    # TODO: Space out points. Scale to larger image?
    # TODO: make relationships different colors
    # Check input and define positions.
    if fixed is None:
        if positions is None:
            pos = nx.spring_layout(graph, fixed=fixed)
        else:
            pos = positions
    else:
        if positions is not None:
            print("WARNING: `fixed` overrides `positions`:\nfixed = {fixed}".format(fixed=fixed),
                  file=sys.stderr)
        pos = nx.spring_layout(graph, fixed=fixed)
    # Draw graph and save.
    nx.draw(graph, pos=pos)
    if fpath is not None:
        print("Writing plot to:\n{fpath}".format(fpath=fpath))
        plt.savefig(fpath, bbox_inches='tight')
    plt.show()
    return None
