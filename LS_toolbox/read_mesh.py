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


def parse_elements(model_dict, keyword_filter=""):
    """
    Parse elements from a model dictionary (from read_keyfile.read_keyfile_dict)
    into a structured dictionary grouped by part id (pid).

    :param model_dict: Dictionary {keyword: [[lines]]} from read_keyfile_dict.
    :param keyword_filter: Additional filter string (e.g. "SOLID" to match "ELEMENT_SOLID").
    :return: (parsed_dict, comments)
        - parsed_dict: {pid: [[element_id, node_id1, node_id2, ...]]}
        - comments: {keyword: [(position, content)]} where position is the number of
          elements parsed before the comment in that keyword block.
    """
    # Local import to avoid circular dependency (read_keyfile imports read_mesh)
    from LS_toolbox import read_keyfile as rk

    # Default headers for each known element type
    HEADERS = {
        "SOLID": "$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8",
        "SHELL": "$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8",
        "BEAM":  "$#   eid     pid      n1      n2      n3     rt1     rr1     rt2     rr2   local",
    }

    parsed_dict = {}
    comments = {}

    for keyword, blocks in model_dict.items():
        if "ELEMENT_" not in keyword or keyword_filter not in keyword:
            continue

        # Determine element type from keyword (e.g. "ELEMENT_SOLID" -> "SOLID")
        elem_type = keyword.replace("ELEMENT_", "").split("_")[0]
        header = HEADERS.get(elem_type)
        if header is None:
            continue

        # Flatten blocks into a single list of lines
        lines = [line for block in blocks for line in block]

        entities, kw_comments = rk.parse_keyword(lines, header)
        comments[keyword] = kw_comments

        for entity in entities:
            pid = entity["pid"]
            eid = entity["eid"]
            # Collect all fields except eid and pid, preserving order
            remaining = [v for k, v in entity.items() if k not in ("eid", "pid")]
            if pid not in parsed_dict:
                parsed_dict[pid] = {"type": keyword, "elements": []}
            parsed_dict[pid]["elements"].append([eid] + remaining)

    return parsed_dict, comments

def parse_nodes(model_dict):
    """
    Parse nodes from a model dictionary (from read_keyfile.read_keyfile_dict)
    into a structured dictionary of node_id -> (x, y, z).

    :param model_dict: Dictionary {keyword: [[lines]]} from read_keyfile_dict.
    :return: Dictionary {node_id: (x, y, z)}.
    """
    # Local import to avoid circular dependency (read_keyfile imports read_mesh)
    from LS_toolbox import read_keyfile as rk

    node_dict = {}
    comments = {}
    for keyword, blocks in model_dict.items():
        if keyword != "NODE":
            continue

        # Flatten blocks into a single list of lines
        lines = [line for block in blocks for line in block]

        entities, comments = rk.parse_keyword(lines, "$#   nid               x               y               z      tc      rc")
        for entity in entities:
            node_id = entity["nid"]
            x = entity["x"]
            y = entity["y"]
            z = entity["z"]
            node_dict[node_id] = (x, y, z)

    return node_dict, comments

def parsed_elements_to_model_dict(parsed_elements, model_dict, comments=None):
    """
    Convert parsed elements back into a model dictionary format
    (compatible with read_keyfile.read_keyfile_dict).

    :param parsed_elements: {pid: {"type": keyword, "elements": [[eid, n1, n2, ...]]}}
        as returned by parse_elements.
    :param model_dict: Original model dictionary to update.
    :param comments: {keyword: [(position, content)]} optional comments to re-insert
        (as returned by parse_elements).
    :return: Updated model dictionary with element keywords replaced.
    """
    from LS_toolbox import read_keyfile as rk

    if comments is None:
        comments = {}

    # Default headers for formatting (same as parse_elements)
    HEADERS = {
        "SOLID": "$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8",
        "SHELL": "$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8",
        "BEAM":  "$#   eid     pid      n1      n2      n3     rt1     rr1     rt2     rr2   local",
    }

    # ---- Group elements by keyword type ----
    # {keyword: [[eid, pid, n1, n2, ...], ...]}
    keyword_elements = {}
    for pid, data in parsed_elements.items():
        keyword = data["type"]
        if keyword not in keyword_elements:
            keyword_elements[keyword] = []
        for elem in data["elements"]:
            # elem = [eid, n1, n2, ...] — re-insert pid after eid
            keyword_elements[keyword].append([elem[0], pid] + elem[1:])

    # ---- Rebuild lines for each keyword ----
    for keyword, elements in keyword_elements.items():
        elem_type = keyword.replace("ELEMENT_", "").split("_")[0]
        header_str = HEADERS.get(elem_type)
        if header_str is None:
            continue

        field_defs = rk._parse_header_line(header_str)

        # Build a map  position -> [comment_lines]
        kw_comments = comments.get(keyword, [])
        comment_map = {}
        for pos, content in kw_comments:
            comment_map.setdefault(pos, []).append(content)

        lines = []
        for i, elem in enumerate(elements):
            # Re-insert comments that appeared before this element
            for c in comment_map.get(i, []):
                lines.append(c)

            # Format the element as a fixed-width line
            line = ""
            for j, (_, field_width) in enumerate(field_defs):
                if j < len(elem):
                    val = elem[j]
                    if isinstance(val, float):
                        line += f"{val:{field_width}.6e}"
                    elif isinstance(val, int):
                        line += f"{val:{field_width}d}"
                    else:
                        line += f"{str(val):>{field_width}}"
                else:
                    line += " " * field_width
            lines.append(line)

        # Trailing comments (after last element)
        for c in comment_map.get(len(elements), []):
            lines.append(c)

        # Replace the keyword blocks in model_dict with one single block
        model_dict[keyword] = [lines]

    return model_dict


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

