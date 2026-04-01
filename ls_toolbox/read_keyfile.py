from ls_toolbox import read_mesh as rm
import re


# Read nodes coordinates from a .k file.
# def read_nodes(file_path: str) -> dict:
#     """
#     Read a .k file and return the nodes coordinates.
#     :param file_path: Path to the .k file.
#     :return: Dictionary of nodes coordinates {node_id: [x, y, z]}.
#     """
#     nodes_list = rm.read_nodes(file_path)
#     nodes = {}
#     for node in nodes_list:
#         nodes[node[0]] = node[1:]
#     return nodes

def read_keyfile(file_path: str) -> list:
    """
    Read a .k file and return a list of lines.
    :param file_path: Path to the .k file.
    :return: List of lines in the key file.
    """
    with open(file_path, 'r') as f:
        # Read after the line "*KEYWORD"
        for line in f:
            if line.startswith('*KEYWORD'):
                break
        # Read until the line "*END"
        file = []
        for line in f:
            if line.startswith('*END'):
                break
            file.append(line)
    return file

def read_keyfile_dict(file_path: str) -> dict:
    """
    Read a .k file and return a dictionary of keywords and their lines.
    :param file_path: Path to the .k file.
    :return: Dictionary of keywords and their lines {keyword: [[lines]]}.
    """
    with open(file_path, 'r') as f:
        file = {}
        file["START_OF_FILE"] = []
        # Read after the line "*KEYWORD"
        for line in f:
            if line.startswith('*KEYWORD'):
                # Get back one line before
                break
            file["START_OF_FILE"].append(line)
        # Read until the line "*END"
        keyword = "KEYWORD"
        file[keyword] = [[]]
        for line in f:
            if line.startswith('*END'):
                break
            if line.startswith("*"):
                keyword = line.replace("*", "").replace("\n", "")
                if keyword not in file:
                    file[keyword] = []
                file[keyword].append([])
            else:
                file[keyword][-1].append(line.replace("\n", ""))
        file["END_OF_FILE"] = []
        for line in f:
            file["END_OF_FILE"].append(line)
    return file

def _parse_header_line(header_line):
    """
    Parse a single header line to extract field names and their widths.
    Field widths are deduced from the position of each field name in the header.
    Field names are assumed to be right-aligned within their column.

    :param header_line: Header string, e.g. "$#   eid     pid      n1      n2 ...".
    :return: List of (field_name, field_width) tuples.

    Examples:
        8-char fields:  "$#   eid     pid      n1      n2"  -> [("eid",8), ("pid",8), ("n1",8), ("n2",8)]
        16-char fields: "$#            a1              a2"  -> [("a1",16), ("a2",16)]
        80-char title:  "$#                          title" -> [("title",80)]  (if line is 80 chars)
    """
    # Replace the "$#" prefix with spaces to preserve column positions
    if header_line.startswith("$#"):
        line = "  " + header_line[2:]
    else:
        line = header_line

    fields = []
    prev_end = 0
    for match in re.finditer(r'\S+', line):
        name = match.group()
        end = match.end()
        width = end - prev_end
        fields.append((name, width))
        prev_end = end

    return fields


def parse_keyword(lines, headers):
    """
    Generic parser for LS-DYNA keyword data lines.
    Parses fixed-width data lines according to the field structure defined by
    one or more header lines.  The number of header lines determines how many
    consecutive data lines make up a single entity.

    :param lines: List of data lines from a keyword block.
    :param headers: Header line (str) or list of header lines (list[str])
        defining the entity structure.

        Single-line entity example:
            "$#   eid     pid      n1      n2      n3     rt1     rr1     rt2     rr2   local"

        Multi-line entity example (3 lines per entity):
            ["$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8",
             "$#            a1              a2              a3",
             "$#            d1              d2              d3"]

        Two-line entity example (title + data):
            ["$#                                                                         title",
             "$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid"]

    :return: (entities, comments)
        - entities: List of dicts, each dict mapping field names to parsed values.
        - comments: List of (position, content) tuples, where position is the
          number of entities parsed before the comment was encountered.
    """
    if isinstance(headers, str):
        headers = [headers]

    # Parse each header line to obtain [(field_name, field_width), ...]
    field_defs = [_parse_header_line(h) for h in headers]
    n_lines_per_entity = len(headers)

    entities = []
    comments = []
    entity_count = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            i += 1
            continue

        # Save comments with their position
        if line.strip().startswith("$"):
            comments.append((entity_count, line))
            i += 1
            continue

        # Parse one entity (may span n_lines_per_entity consecutive lines)
        entity = {}
        for line_idx in range(n_lines_per_entity):
            if i + line_idx >= len(lines):
                break
            data_line = lines[i + line_idx]
            pos = 0
            for field_name, field_width in field_defs[line_idx]:
                raw = data_line[pos:pos + field_width].strip()
                try:
                    entity[field_name] = int(raw)
                except ValueError:
                    try:
                        entity[field_name] = float(raw)
                    except ValueError:
                        entity[field_name] = raw
                pos += field_width

        entities.append(entity)
        entity_count += 1
        i += n_lines_per_entity

    return entities, comments

def get_ids(key: str, list_lines) -> list:
    """
    Get the ids of the given key in the .k file.
    :param key: Key.
    :param list_lines: List of lines in the .k file.
    :return: List of ids.
    """
    var_len = 10
    if key in ["*NODE", "*ELEMENT_SOLID"]:
        var_len = 8
    ids = []
    i = 0
    while i < len(list_lines):
        if list_lines[i].startswith(key):
            i += 2
            while not (list_lines[i].startswith("*") or list_lines[i].startswith("$")):
                ids.append(int(list_lines[i][:var_len]))
                i += 1
                if i == len(list_lines):
                    break
        i += 1
    return ids

def read_elements(file_path: str, elements_keyword="ELEMENT_SOLID") -> list:
    """
    Read a .k file and return the elements.
    :param file_path: Path to the .k file.
    :return: List of elements [[element_id, node_id1, node_id2, ...]].
    """
    elements = rm.read_elements(file_path, keyword=elements_keyword)
    return elements
