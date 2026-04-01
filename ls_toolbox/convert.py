# Conversion tools to convert mesh from other formats to LS-DYNA format

import numpy as np
from ls_toolbox import write_keyfile as wk


def read_cdbfile(path, exclude_elems_array=None, type='Tet'):
    """
    Extract the elements number and their associated material from a cdb mesh file.
    :param path: Path to the cdb file.
    :return: Elements number array and associated materials, Nodes and associated coordinates x, y and z arrays.
    """

    # EXTRACTING THE TABLES OF CONNECTION AND COORDINATES
    materials = []  # Material property number
    elems = []  # Table of connection
    nodes = []  # Table of coordinates
    x = []  # x-coordinates
    y = []  # y-coordinates
    z = []  # z-coordinates
    with open(path, 'r', errors="ignore") as f:
        # Open the mesh_file_path file to extract the table of connection and the table of coordinates.
        extract_nodes = False
        extract_elems = False
        line = f.readline()
        while line:
            if extract_nodes:
                if line.find("-1,") != -1:
                    extract_nodes = False
                    line = f.readline()
                    continue
                nodes.append(int(line[:NODE_LEN]))
                x.append(float(line[NODE_PROPERTIES_NB * NODE_LEN:3 * NODE_LEN + COORD_LEN]))
                y.append(float(line[NODE_PROPERTIES_NB * NODE_LEN + COORD_LEN:3 * NODE_LEN + COORD_LEN * 2]))
                try:
                    z.append(float(line[NODE_PROPERTIES_NB * NODE_LEN + COORD_LEN * 2:3 * NODE_LEN + COORD_LEN * 3]))
                except ValueError:
                    z.append(0)
                line = f.readline()
                continue
            if extract_elems:
                if line.find("-1") != -1:
                    extract_elems = False
                    line = f.readline()
                    continue
                if IS2LINES:
                    line += f.readline()
                line = line.replace("\n", '')
                materials.append(int(line[:ELEM_LEN]))
                line_elem = [int(line[i * ELEM_LEN:(i + 1) * ELEM_LEN]) for i in
                             range(ELEM_START, len(line) // ELEM_LEN)]
                elems.append(line_elem)
                line = f.readline()
                continue

            # DETECTING TABLE OF COORDINATE (NODES)
            if line.find("NBLOCK") != -1:
                line = f.readline()
                NODE_LEN = int(line.split(',')[0].replace('(', '').split('i')[1])
                NODE_PROPERTIES_NB = 3  # line.split(',')[0].replace('(', '').split('i')[0]
                COORD_LEN = int(line.split(',')[1].split('.')[0].split('e')[1])
                extract_nodes = True
                line = f.readline()
                continue

            # DETECTING TABLE OF CONNECTION (ELEMENTS)
            if line.find("EBLOCK") != -1:
                line = f.readline()
                ELEM_LEN = int(line.split(',')[0].replace(')', '').split('i')[1])
                ELEM_START = 10  # Table of connection doesn't start before the 10th value
                extract_elems = True
                line = f.readline()
                IS2LINES = False
                curs_pos = f.tell()
                sec_line = f.readline()
                if len(line) != len(sec_line):
                    IS2LINES = True
                f.seek(curs_pos)
                continue

            line = f.readline()

    elems = np.array(elems)
    materials = np.array(materials)
    nodes = np.array(nodes)
    x = np.array(x)
    y = np.array(y)
    z = np.array(z)

    if exclude_elems_array is not None:
        mask_exclude_elems = np.zeros(len(elems))
        mask_exclude_elems[exclude_elems_array.astype(int)] = 1
        mask_exclude_elems = mask_exclude_elems.astype(bool)
        elems = elems[~mask_exclude_elems]
        materials = materials[~mask_exclude_elems]

    return elems, materials, nodes, x, y, z
def cdb2dynamesh(cdb_path, out_path=None):
    """
    Convert an ANSYS CDB mesh file to LS-DYNA mesh format.
    :param cdb_path: Path to the ANSYS CDB file.
    :param out_path: Path to the output LS-DYNA mesh file (.k file).
    :return: None
    """
    # Read the cdb file
    elems, materials, nodes, x, y, z = read_cdbfile(cdb_path)
    # change the 8th column position to the last position
    elems = np.array([elem[[0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 8]] for elem in elems])

    # Create keys
    node_array = np.array([nodes, x, y, z]).T
    list_lines = []
    part_id = wk.add_part(list_lines)
    wk.add_nodes(list_lines, node_array)
    wk.add_element_solids(list_lines, part_id, elems)
    if out_path is None:
        out_path = cdb_path.replace(".cdb", ".k")
    wk.write_keyfile(list_lines, out_path)



