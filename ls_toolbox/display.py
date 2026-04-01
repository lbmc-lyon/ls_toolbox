import pyvista as pv
import numpy as np
from ls_toolbox import read_keyfile as rk

def keyword2pvmesh(file_path: str) -> pv.UnstructuredGrid:
    """
    Convert a .k file to a pyvista mesh.
    :param file_path: Path to the .k file.
    :return: Pyvista mesh (UnstructuredGrid).
    """
    nodes = rk.read_nodes(file_path)
    elements = rk.read_elements(file_path)
    nodes_coords = np.array([nodes[node_id] for node_id in nodes.keys()])
    # Create a dictionary to convert node ids to node index
    node_ids_to_node_index = dict()
    for i, node_id in enumerate(nodes.keys()):
        node_ids_to_node_index[node_id] = i
    cells = np.array([element[2:] for element in elements])
    # Cells to node index
    for i, cell in enumerate(cells):
        for j, node_id in enumerate(cell):
            cells[i][j] = node_ids_to_node_index[node_id]

    node_nb_per_elem = np.array([len(el) - 2 for el in elements])
    cell_types = np.array([pv.CellType.HEXAHEDRON if len(cell) == 8 else pv.CellType.TETRA for cell in cells])
    cells = np.column_stack((node_nb_per_elem, cells))
    mesh = pv.UnstructuredGrid(cells, cell_types, nodes_coords)

    return mesh