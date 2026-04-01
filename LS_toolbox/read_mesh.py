from dynareadout import key_file_parse
import numpy as np
import pyvista as pv


def read_nodes(mesh_file_path):
    """
    Read a mesh file and return the nodes and elements.
    :param mesh_file_path: Path to the mesh file.
    :return: Nodes and elements.
    """
    keywords = key_file_parse(mesh_file_path)

    # EXTRACT NODES
    node_keywords = keywords["NODE"]
    node_table = []
    # Loop over all *NODE keywords
    for i in range(len(node_keywords)):
        # Loop over all cards of each *NODE keyword
        for j in range(len(node_keywords[i])):
            node = node_keywords[i][j]
            # Then you can parse the variables of each card as integers and floats
            # The list of integers holds all the widths of each variable in the card in characters
            nid, x, y, z = node.parse_whole([8, 16, 16, 16])
            node_table.append([nid, x, y, z])
    return node_table


def read_elements(mesh_file_path, keyword="ELEMENT_SOLID"):
    """
    Read a mesh file and return the elements and associated node ids.
    :param mesh_file_path: Path to the mesh file.
    :param keyword: Keyword to search for in the mesh file.
    :return: Elements table (elements and node ids) [[elem_id, part_id, node_id1, node_id2, ...]].
    """
    skip_ortho = False
    if "ORTHO" in keyword:
        skip_ortho = True
    keywords = key_file_parse(mesh_file_path)

    # EXTRACT ELEMENTS
    elem_keywords = keywords[keyword]
    elem_table = []
    # Loop over all *ELEMENT keywords
    for i in range(len(elem_keywords)):
        # Loop over all cards of each *ELEMENT keyword
        for j in range(len(elem_keywords[i])):
            if skip_ortho:
                if not j % 3 == 0:
                    continue
            elem = elem_keywords[i][j]
            # Then you can parse the variables of each card as integers and floats
            # The list of integers holds all the widths of each variable in the card in characters
            eid, pid, n1, n2, n3, n4, n5, n6, n7, n8 = elem.parse_whole([8, 8, 8, 8, 8, 8, 8, 8, 8, 8])
            elem_table.append([eid, pid, n1, n2, n3, n4, n5, n6, n7, n8])
    # Remove zero sum value columns
    elem_table = np.array(elem_table)
    elem_table = elem_table[:, np.sum(elem_table, axis=0) != 0]
    return elem_table

def read_elements_dict(model_dict, keyword_filter=""):
    """
    Read elements from a model dictionary (returned by read_keyfile.read_keyfile_dict).
    Returns a dictionary of element types and their lines from all keywords
    containing "ELEMENT_" and the optional keyword_filter.
    :param model_dict: Dictionary of keywords and their lines {keyword: [[lines]]}.
    :param keyword_filter: Additional filter string (e.g. "SOLID" to match "ELEMENT_SOLID").
    :return: Dictionary {keyword: [lines]} for each matching ELEMENT keyword.
    """
    elem_dict = {}
    for keyword, blocks in model_dict.items():
        if "ELEMENT_" in keyword and keyword_filter in keyword:
            elem_dict[keyword] = []
            for block in blocks:
                elem_dict[keyword].extend(block)
    return elem_dict


def create_mesh(node_table, elem_table):
    """
    Create a mesh from the nodes and elements tables.
    :param node_table: Nodes table.
    :param elem_table: Elements table.
    :return: Mesh.
    """
    # Convert to pyvista mesh
    nodes = np.array(node_table)[:, 1:4]
    nodes = nodes.astype(float)
    cells = np.array(elem_table)[:, 2:]
    cells = cells.astype(int)
    # Converting node ids to node indices
        # Create a dictionary that maps node ids to their indices
    node_id_to_index = {node_id: index for index, node_id in enumerate(np.array(node_table)[:, 0])}
        # Use the dictionary to convert node ids to node indices in the cells array
    for i in range(len(cells)):
        for j in range(len(cells[i])):
            cells[i, j] = node_id_to_index[cells[i, j]]

    # Adding the number of nodes per cell
    cells = np.insert(cells, 0, cells.shape[1], axis=1)
    if cells.shape[1] - 1 == 8:
        cellstype = pv.CellType.HEXAHEDRON
    elif cells.shape[1] - 1 == 4:
        cellstype = pv.CellType.QUAD
    mesh = pv.UnstructuredGrid(cells, [cellstype] * len(cells), nodes)
    return mesh

