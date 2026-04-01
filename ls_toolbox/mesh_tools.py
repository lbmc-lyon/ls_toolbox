"""
Mesh topology tools for LS-DYNA models.
Functions to analyse face connectivity and identify surface nodes.
"""

from collections import Counter

# Hexahedron – 8 nodes, 6 quadrilateral faces (LS-DYNA node ordering)
HEX_FACES = [
    (0, 1, 2, 3),  # bottom
    (4, 5, 6, 7),  # top
    (0, 1, 5, 4),  # front
    (1, 2, 6, 5),  # right
    (2, 3, 7, 6),  # back
    (3, 0, 4, 7),  # left
]

# Tetrahedron – 4 nodes, 4 triangular faces
TET_FACES = [
    (0, 1, 2),
    (0, 1, 3),
    (1, 2, 3),
    (0, 2, 3),
]


def _classify_element(raw_nodes):
    """
    Determine the element type and return a clean, ordered node list.

    Handles both storage conventions:
      - zero-padded tetrahedra  : [n1, n2, n3, n4, 0, 0, 0, 0]
      - degenerate hexahedra    : [n1, n2, n3, n4, n4, n4, n4, n4]

    :param raw_nodes: List of node IDs as stored in the element.
    :return: (elem_type, nodes)
        - elem_type: "hex", "tet", or None if unsupported.
        - nodes: Cleaned node list suitable for indexing with HEX_FACES / TET_FACES.
    """
    # Remove zero-padding
    nonzero = [n for n in raw_nodes if n != 0]
    n_unique = len(set(nonzero))

    if n_unique == 8:
        return "hex", nonzero[:8]

    if n_unique == 4:
        # Keep only the first occurrence of each node, preserving order
        seen = set()
        ordered = []
        for n in nonzero:
            if n not in seen:
                seen.add(n)
                ordered.append(n)
        return "tet", ordered[:4]

    # Unsupported element type (wedge, pyramid, …)
    return None, nonzero


def _element_faces(raw_nodes):
    """
    Return the faces of an element as a list of frozensets of node IDs.

    :param raw_nodes: List of node IDs (n1 … n8) for the element.
    :return: List of frozensets, each representing one face.
    """
    elem_type, nodes = _classify_element(raw_nodes)

    if elem_type == "hex":
        face_defs = HEX_FACES
    elif elem_type == "tet":
        face_defs = TET_FACES
    else:
        return []

    return [frozenset(nodes[i] for i in fd) for fd in face_defs]


def build_face_connectivity(parsed_elements):
    """
    Build face connectivity: count how many elements share each face.

    :param parsed_elements: Dict as returned by ``read_mesh.parse_elements``:
        ``{pid: {"type": keyword, "elements": [[eid, n1, n2, ...], ...]}}``
    :return: ``Counter`` mapping each face (frozenset of node IDs) to the
        number of elements that contain it.
    """
    face_count = Counter()

    for pid_data in parsed_elements.values():
        for elem in pid_data["elements"]:
            # elem = [eid, n1, n2, …]
            nodes = elem[1:]
            for face in _element_faces(nodes):
                face_count[face] += 1

    return face_count


def get_surface_faces(parsed_elements):
    """
    Identify the faces on the surface of the mesh (connected to exactly one
    element).

    :param parsed_elements: Dict from ``read_mesh.parse_elements``.
    :return: List of frozensets, each representing a surface face.
    """
    face_count = build_face_connectivity(parsed_elements)
    return [face for face, count in face_count.items() if count == 1]


def get_surface_nodes(parsed_elements):
    """
    Identify the nodes that lie on the surface of the mesh.

    A node is on the surface if it belongs to at least one face that is *not*
    shared by two elements (i.e. the face appears only once in the
    connectivity).

    :param parsed_elements: Dict from ``read_mesh.parse_elements``:
        ``{pid: {"type": keyword, "elements": [[eid, n1, n2, ...], ...]}}``
    :return: Sorted list of surface node IDs.
    """
    surface_faces = get_surface_faces(parsed_elements)
    surface_node_set = set()
    for face in surface_faces:
        surface_node_set.update(face)
    return sorted(surface_node_set)

