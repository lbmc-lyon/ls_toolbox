# LS_toolbox
A collection of tools for working with LS-DYNA and LS-PrePost.

## Installation
`pip install LS_toolbox`

Create environment variables named `LSDYNA_PATH` and `LSPREPOST_PATH` and set them to the paths of the LS-DYNA and LS-PrePost executables, respectively.\
To do this, open the terminal and type:

For Windows:
```bash
setx LSDYNA_PATH "path\to\lsdyna\executable"
setx LSPREPOST_PATH "path\to\lsprepost\executable"
```
For Linux:
```bash
export LSDYNA_PATH="path/to/lsdyna/executable"
export LSPREPOST_PATH="path/to/lsprepost/executable"
```

## Example usage 
### Copy/paste and run as it is:

```python
import ls_toolbox as lst
import pyvista as pv
import os
import subprocess
import numpy as np

"""
Example using a beam 3D mesh .k file.
The mesh is first displayed using PyVista.
Then a finite element model is created by setting the boundary conditions (traction test) and material properties.
Finally, the simulation is run using LS-Dyna and the d3plot file is opened in LS-PrePost.
Simulation files are cleared at the end (except for the .K file of the FE model).
"""

# get ls_toolbox path
lst_path = os.path.dirname(lst.__file__)

# Path to the example keyfile
file_path = os.path.join(lst_path, "Example/Beam_3D_mesh_example.k")

# Read the keyfile
keyfile_lines = lst.read_keyfile.read_keyfile(file_path)

# Visualize the mesh with PyVista
mesh = lst.display.keyword2pvmesh(file_path)
mesh.plot(show_edges=True)

# Get the nodes from the keyfile
nodes = lst.read_keyfile.read_nodes(file_path)
ids = np.array(list(nodes.keys()))
coords = np.array(list(nodes.values()))

# Add a fixed displacement on the bottom nodes
# Get the nodes on the bottom face
bottom_nodes = ids[coords[:, 2] == min(coords[:, 2])]
lst.write_keyfile.add_spc(keyfile_lines, bottom_nodes)

# Add a prescribed motion on the top nodes
# Get the nodes on the top face
top_nodes = ids[coords[:, 2] == max(coords[:, 2])]
lst.write_keyfile.add_prescribed_motion_velocity(keyfile_lines, top_nodes, 1.)  # Only along the z axis

# Add a section
section_id = lst.write_keyfile.add_section_solid(keyfile_lines)

# Add a material elastic linear
material_data = np.array([1000, 1e6, 0.4999])  # rho, E, nu
material_id = lst.write_keyfile.add_mat_elastic(keyfile_lines, material_data)

# Modify the part to set the section and material data
part_id = 1
lst.write_keyfile.modify_part(keyfile_lines, part_id, section_id, material_id)

# Add an implicit solver
lst.write_keyfile.add_implicit_solver(keyfile_lines, dt0=0.5)

# Add termination time
lst.write_keyfile.add_termination(keyfile_lines, 30.)

# Add d3plot output
lst.write_keyfile.add_d3plot(keyfile_lines, dt=0.5)

# Write the new keyfile
new_file_path = file_path.replace(".k", "_model.k")
lst.write_keyfile.write_keyfile(keyfile_lines, new_file_path)

# Run LS-Dyna
print("Running LS-Dyna...")
lst.prepost_commands.run_lsdyna(new_file_path)
print("Done.")

# Open the d3plot file in PrePost
subprocess.check_call(
    f"\"{lst.prepost_commands.LS_PREPOST_PATH}\" {os.path.join(os.path.split(new_file_path)[0], 'd3plot')}", shell=True)

# Clear simulation files
lst.clear_sim_files.clear_sim_files(os.path.split(new_file_path)[0])
```