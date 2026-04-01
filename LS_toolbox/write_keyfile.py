import numpy as np
from datetime import datetime
from LS_toolbox import read_keyfile as rk


def write_keyfile(list_lines: list, file_path) -> None:
    """
    Write the key file.
    :param list_lines: List of lines in the key file.
    :param file_path: Path to the .k file.
    """
    # Get the current date and time
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    with open(file_path, 'w') as f:
        f.write("$# Custom keyword file\n")
        f.write(f"$# Created on {dt_string}\n")
        f.write('*KEYWORD\n')
        for line in list_lines:
            f.write(line)
        f.write('*END')


def write_keyfile_dict(keyfile_dict: dict, file_path: str) -> None:
    """
    Write a dictionary of keywords and their lines to a .k file.
    :param file_path: Path to the .k file.
    :param keyfile_dict: Dictionary of keywords and their lines {keyword: [[lines]]}.
    """
    with open(file_path, 'w') as f:
        # Write the start of the file
        for line in keyfile_dict["START_OF_FILE"]:
            f.write(line)

        # Write the keywords and their lines
        for keyword, blocks in keyfile_dict.items():
            if keyword not in ["START_OF_FILE", "END_OF_FILE"]:
                for block in blocks:
                    f.write(f"*{keyword}\n")
                    for line in block:
                        f.write(f"{line}\n")
        f.write("*END\n")

        # Write the end of the file
        for line in keyfile_dict["END_OF_FILE"]:
            f.write(line)


def write_model_dict(model_dict: dict, file_path: str) -> None:
    """
    Write a model dictionary (from read_keyfile.read_keyfile_dict, possibly
    modified by parsed_elements_to_model_dict / parsed_nodes_to_model_dict)
    to an LS-DYNA keyword file (.k).

    Handles the special meta-keys START_OF_FILE, KEYWORD and END_OF_FILE
    that are created by read_keyfile_dict.

    :param model_dict: Dictionary {keyword: [[lines]]} representing the model.
    :param file_path:  Output file path.
    """
    META_KEYS = {"START_OF_FILE", "KEYWORD", "END_OF_FILE"}

    with open(file_path, 'w') as f:
        if "START_OF_FILE" in model_dict:
            for line in model_dict["START_OF_FILE"]:
                f.write(line)

        f.write("*KEYWORD\n")
        # Write optional lines that were stored under the KEYWORD key
        if "KEYWORD" in model_dict:
            for block in model_dict["KEYWORD"]:
                for line in block:
                    f.write(f"{line}\n")

        for keyword, blocks in model_dict.items():
            if keyword in META_KEYS:
                continue
            for block in blocks:
                f.write(f"*{keyword}\n")
                for line in block:
                    f.write(f"{line}\n")

        f.write("*END\n")

        if "END_OF_FILE" in model_dict:
            for line in model_dict["END_OF_FILE"]:
                f.write(line)


def add_node_set(list_lines: list, node_ids: np.ndarray) -> int:
    """
    Add node set to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param node_ids: List of node ids that will be in the node set.
    :return: Node set id.
    """
    node_set_key = "*SET_NODE_LIST"
    # Check ids if node sets already exist in the file
    node_set_ids = rk.get_ids(node_set_key, list_lines)
    node_set_id = max(node_set_ids) + 1 if node_set_ids else 1
    # Add the node set
    node_set_lines = []
    node_set_lines.append(f"{node_set_key}\n")
    node_set_lines.append("$#     sid       da1       da2       da3       da4    solver       its         -\n")
    node_set_lines.append(f"{node_set_id: 10}       0.0       0.0       0.0       0.0MECH      1                  \n")
    node_set_lines.append("$#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8\n")
    nodes_line = ""
    for i, node in enumerate(node_ids):
        nodes_line += f"{node: 10}"
        if (i+1) % 8 == 0:
            node_set_lines.append(nodes_line + "\n")
            nodes_line = ""
    if nodes_line:
        node_set_lines.append(nodes_line + " " * (80 - len(nodes_line)) + "\n")
    # Add the lines to the list
    list_lines.extend(node_set_lines)
    return node_set_id

def add_spc(list_lines: list, node_ids: np.ndarray) -> None:
    """
    Add spc boundary condition to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param node_ids: List of node ids that will be fixed.
    """
    spc_key = "*BOUNDARY_SPC_SET"

    # Add the node set
    node_set_id = add_node_set(list_lines, node_ids)

    # Add the spc boundary condition
    # Check ids if the spc boundary conditions already in the file
    spc_lines = []
    spc_lines.append(f"{spc_key}\n")
    spc_lines.append("$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz\n")
    spc_lines.append(f"{node_set_id: 10}         0         1         1         1         1         1         1\n")
    # Add the lines to the list
    list_lines.extend(spc_lines)
    return

def add_curve(list_lines: list, curve_data: np.ndarray) -> int:
    """
    Add curve to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param curve_data: Curve data [[x, y]].
    :return: Curve id.
    """
    curve_key = "*DEFINE_CURVE"
    # Check ids if curves already exist in the file
    curve_ids = rk.get_ids(curve_key, list_lines)
    curve_id = max(curve_ids) + 1 if curve_ids else 1
    # Add the curve
    curve_lines = []
    curve_lines.append(f"{curve_key}\n")
    curve_lines.append("$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint\n")
    curve_lines.append(f"{curve_id: 10}         0       1.0       1.0       0.0       0.0         0         0\n")
    curve_lines.append("$#                a1                  o1\n")
    for i, data in enumerate(curve_data):
        curve_lines.append(f"{data[0]: .13E}{data[1]: .13E}\n")
    # Add the lines to the list
    list_lines.extend(curve_lines)
    return curve_id

def add_vector(list_lines: list, vector_data: np.ndarray) -> int:
    """
    Add vector to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param vector_data: Vector data [x, y, z].
    :return: Vector id.
    """
    vector_key = "*DEFINE_VECTOR"
    # Check ids if vectors already exist in the file
    vector_ids = rk.get_ids(vector_key, list_lines)
    vector_id = max(vector_ids) + 1 if vector_ids else 1
    # Add the vector
    vector_lines = []
    vector_lines.append(f"{vector_key}\n")
    vector_lines.append("$#     vid        xt        yt        zt        xh        yh        zh       cid\n")
    vector_lines.append(f"{vector_id: 10}       0.0       0.0       0.0{vector_data[0]: .3E}{vector_data[1]: .3E}{vector_data[2]: .3E}         0\n")
    # Add the lines to the list
    list_lines.extend(vector_lines)
    return vector_id

def add_prescribed_motion_velocity(list_lines: list, node_ids: np.ndarray, velocity: float) -> None:
    """
    Add prescribed motion velocity to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param node_ids: List of node ids that will be prescribed motion.
    :param velocity: Prescribed motion velocity.
    """
    key = "*BOUNDARY_PRESCRIBED_MOTION_SET"

    # Add the node set
    node_set_id = add_node_set(list_lines, node_ids)

    # Add the curve
    curve_id = add_curve(list_lines, np.array([[0, velocity], [1e99, velocity]]))

    # Add the vector
    vector_id = add_vector(list_lines, np.array([0, 0, 1]))  # Along z-axis

    # Add the prescribed motion boundary condition
    spc_lines = []
    spc_lines.append(f"{key}\n")
    spc_lines.append("$#    nsid       dof       vad      lcid        sf       vid     death     birth\n")
    spc_lines.append(f"{node_set_id: 10}        -4         0{curve_id: 10}         1{vector_id: 10}1.00000E28       0.0\n")
    # Add the lines to the list
    list_lines.extend(spc_lines)

def add_section_solid(list_lines: list) -> int:
    """
    Add section solid to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :return: Section id.
    """
    section_key = "*SECTION_SOLID"
    # Check ids if sections already exist in the file
    section_ids = rk.get_ids(section_key, list_lines)
    section_id = max(section_ids) + 1 if section_ids else 1
    # Add the section
    section_lines = []
    section_lines.append(f"{section_key}\n")
    section_lines.append("$#   secid    elform       aet    unused    unused    unused    cohoff   gaskeit\n")
    section_lines.append(f"{section_id: 10}         1         0                                     0.0       0.0\n")
    # Add the lines to the list
    list_lines.extend(section_lines)
    return section_id

def add_mat_elastic(list_lines: list, material_data: np.ndarray) -> int:
    """
    Add material elastic to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param material_data: Material data [rho, E, nu].
    :return: Material id.
    """
    material_key = "*MAT_ELASTIC"
    # Check ids if materials already exist in the file
    material_ids = rk.get_ids(material_key, list_lines)
    material_id = max(material_ids) + 1 if material_ids else 1
    # Add the material
    material_lines = []
    material_lines.append(f"{material_key}\n")
    material_lines.append("$#     mid        ro         e        pr        da        db  not used\n")
    material_lines.append(f"{material_id: 10}{material_data[0]: 10}{material_data[1]: .3e}{material_data[2]: 10}       0.0       0.0       0.0\n")
    # Add the lines to the list
    list_lines.extend(material_lines)
    return material_id

def add_mat_ogden(list_lines: list, material_data: np.ndarray) -> int:
    """
    Add material Ogden (MAT_077) to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param material_data: Material data [rho, nu, mu1, alpha1].
    :return: Material id.
    """
    material_key = "*MAT_OGDEN_RUBBER"
    # Check ids if materials already exist in the file
    material_ids = rk.get_ids(material_key, list_lines)
    material_id = max(material_ids) + 1 if material_ids else 1
    # Add the material
    material_lines = []
    material_lines.append(f"{material_key}\n")
    material_lines.append("$#     mid        ro        pr         n        nv         g      sigf       ref\n")
    material_lines.append(f"{material_id: 10}{material_data[0]: .3E}{material_data[1]: .3E}         0         6       5.0       0.0       0.0\n")
    material_lines.append("$#     mu1       mu2       mu3       mu4       mu5       mu6       mu7       mu8\n")
    material_lines.append(f"{material_data[2]: .3E}                                                                      \n")
    material_lines.append("$#   alpha1    alpha2    alpha3    alpha4    alpha5    alpha6    alpha7    alpha8\n")
    material_lines.append(f"{material_data[3]: .3E}                                                                      \n")
    # Add the lines to the list
    list_lines.extend(material_lines)
    return material_id

def modify_part(list_lines: list, part_id: int, section_id: int, material_id: int) -> None:
    """
    Modify part in a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param part_id: Part id.
    :param section_id: Section id.
    :param material_id: Material id.
    """
    part_key = "*PART"
    # Modify the part
    i = 0
    while i < len(list_lines):
        if list_lines[i].startswith(part_key):
            i += 1
            while not list_lines[i].startswith("*"):
                try:
                    part_id_line = int(list_lines[i][:10])
                    if part_id_line == part_id:
                        list_lines[i] = f"{part_id: 10}{section_id: 10}{material_id: 10}{list_lines[i][30:]}"
                        return
                    i += 1
                except ValueError:
                    i += 1
                    continue

        i += 1

def modify_elementsolid2ortho(list_lines: list, a: np.ndarray, d: np.ndarray) -> None:
    """
    Modify element solid to solid_ortho in a .k file.
    :param a: Vector of first principal direction.
    :param b: Vector of second principal direction.
    """
    part_key = "*ELEMENT_SOLID"
    # Modify the part
    i = 0
    while i < len(list_lines):
        if list_lines[i].startswith(part_key):
            list_lines[i] = "*ELEMENT_SOLID_ORTHO\n"
            i_begin = i
            i += 2
            while not list_lines[i].startswith("*"):
                try:
                    if i == i_begin + 2:
                        # insert a line after ith line
                        list_lines.insert(i+1, "$#            a1              a2              a3\n")
                        i += 1
                    list_lines.insert(i+1, f"{a[0]: 16}{a[1]: 16}{a[2]: 16}\n")
                    i += 1
                    if i == i_begin + 4:
                        # insert a line after ith line
                        list_lines.insert(i+1, "$#            d1              d2              d3\n")
                        i += 1
                    list_lines.insert(i+1, f"{d[0]: 16}{d[1]: 16}{d[2]: 16}\n")
                    i += 1
                except Exception as e:
                    print(e)
                    i += 1
                i += 1
            break
        i += 1

def check_mat_ortho_param(material_data: np.ndarray) -> bool:
    Ea = material_data[1]
    Eb = material_data[2]
    Ec = material_data[3]
    nuba = material_data[4]
    nuca = material_data[5]
    nucb = material_data[6]

    nuab = Ea * nuba / Eb
    nubc = Eb * nucb / Ec
    nuac = Ea * nuca / Ec

    if nuab > 0.5 or nubc > 0.5 or nuac > 0.5:
        print("Warning: mechanical parameters are not valid for orthotropic material.")
        print("Check relations between Elastic moduli and Poisson's ratios.")
        print(f"nuab={nuab}, nubc={nubc}, nuac={nuac}")
        return False
    else:
        return True

def add_mat_ortho(list_lines: list, material_data: np.ndarray) -> int:
    """
    Add material orthotropic to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param material_data: Material data [rho, Ea, Eb, Ec, nuba, nuca, nucb, Gab, Gbc, Gca].
    :return: Material id.
    """
    check_mat_ortho_param(material_data)
    material_key = "*MAT_ORTHOTROPIC_ELASTIC"
    # Check ids if materials already exist in the file
    material_ids = rk.get_ids(material_key, list_lines)
    material_id = max(material_ids) + 1 if material_ids else 1
    # Add the material
    material_lines = []
    material_lines.append(f"{material_key}\n")
    material_lines.append("$#     mid        ro        ea        eb        ec      prba      prca      prcb\n")
    material_lines.append(f"{material_id: 10}{material_data[0]: .3E}{material_data[1]: .3E}{material_data[2]: .3E}{material_data[3]: .3E}{material_data[4]: .3E}{material_data[5]: .3E}{material_data[6]: .3E}\n")
    material_lines.append("$#     gab       gbc       gca      aopt         g      sigf\n")
    material_lines.append(f"{material_data[7]: .3E}{material_data[8]: .3E}{material_data[9]: .3E}       2.0                    \n")
    material_lines.append("$#      xp        yp        zp        a1        a2        a3      macf      ihis\n")
    material_lines.append("                                     0.0       0.0       1.0         1          \n")
    material_lines.append("$#      v1        v2        v3        d1        d2        d3      beta       ref\n")
    material_lines.append("                                    -1.0       0.0       0.0                 0.0\n")
    # Add the lines to the list
    list_lines.extend(material_lines)
    return material_id

def add_mat_hgo(list_lines: list, material_data: np.ndarray) -> int:
    """
    Add material Holzapfel-Gasser-Ogden (MAT_295) to a .k file.
    ONLY WORKS WITH EXPLICIT SOLVER.
    :param list_lines: lines in the key file (see read_keyfile).
    :param material_data: Material data [rho, nu, K1, K2].
    :return: Material id.
    """
    material_key = "*MAT_ANISOTROPIC_HYPERELASTIC"
    # Check ids if materials already exist in the file
    material_ids = rk.get_ids(material_key, list_lines)
    material_id = max(material_ids) + 1 if material_ids else 1
    # Add the material
    material_lines = []
    material_lines.append(f"{material_key}\n")
    material_lines.append("$#     mid       rho      aopt\n")
    material_lines.append(f"{material_id: 10}{material_data[0]: .3E}         2\n")
    material_lines.append("$#   title     itype      beta        nu\n")
    material_lines.append(f"ISO               -2      -2.0{material_data[1]: .3E}\n")
    material_lines.append("$#      c1        c2        c3\n")
    material_lines.append(f"{material_data[2]: .3E}                    \n")
    material_lines.append("$#   title     atype    intype        nf\n")
    material_lines.append(f"ANISO             -1         0         1\n")
    material_lines.append("$#   theta         a         b\n")
    material_lines.append(f"       0.0       0.0       1.0\n")
    material_lines.append("$#   ftype      fcid        k1        k2\n")
    material_lines.append(f"         1         0{material_data[3]: .3E}{material_data[4]: .3E}\n")
    material_lines.append(f"$#      xp        yp        zp        a1        a2        a3      macf         -\n")
    material_lines.append("       0.0       0.0       0.0       0.0       0.0       1.0         1          \n")
    material_lines.append(f"$#      v1        v2        v3        d1        d2        d3      beta       ref\n")
    material_lines.append(f"       0.0       0.0       0.0       1.0       0.0       0.0       0.0       0.0\n")

    # Add the lines to the list
    list_lines.extend(material_lines)
    return material_id

def add_mat_soft_tissue(list_lines: list, material_data: np.ndarray) -> int:
    """
    Add material soft tissue to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param material_data: Material data [rho, C1, C2, C3, C4, C5, Bulk modulus, Stretch ratio].
    :return: Material id.
    """
    material_key = "*MAT_SOFT_TISSUE"
    # Check ids if materials already exist in the file
    material_ids = rk.get_ids(material_key, list_lines)
    material_id = max(material_ids) + 1 if material_ids else 1
    # Add the material
    material_lines = []
    material_lines.append(f"{material_key}\n")
    material_lines.append("$#     mid        ro        c1        c2        c3        c4        c5\n")
    material_lines.append(f"{material_id: 10}{material_data[0]: .3E}{material_data[1]: .3E}{material_data[2]: .3E}{material_data[3]: .3E}{material_data[4]: .3E}{material_data[5]: .3E}\n")
    material_lines.append("$#      xk      xlam      fang     xlam0    failsf    failsm   failshr\n")
    material_lines.append(f"{material_data[6]: .3E}{material_data[7]: .3E}                                                  \n")
    material_lines.append("$#    aopt        ax        ay        az        bx        by        bz\n")
    material_lines.append(f"       2.0       0.0       0.0       1.0       1.0       0.0       0.0\n")
    material_lines.append("$#     la1       la2       la3      macf\n")
    material_lines.append("                                       1\n")
    # Add the lines to the list
    list_lines.extend(material_lines)
    return material_id

def add_erosion(list_lines: list, material_id: int, max_princ_stress: float) -> None:
    """
    Add erosion to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param material_id: Material id to which the erosion will be added.
    :param max_princ_stress: Maximum principal stress for erosion.
    """
    erosion_key = "*MAT_ADD_EROSION"
    # Check ids if erosion already exist in the file
    erosion_ids = rk.get_ids(erosion_key, list_lines)
    # Add the erosion
    erosion_lines = []
    erosion_lines.append(f"{erosion_key}\n")
    erosion_lines.append("$#     mid      excl    mxpres     mneps    effeps    voleps    numfip       ncs\n")
    erosion_lines.append(f"{material_id: 10}       0.0       0.0       0.0       0.0       0.0       1.0       1.0\n")
    erosion_lines.append("$*  slsfac    rwpnal    islchk    shlthk    penopt    thkchg     orien    enmass\n")
    erosion_lines.append("$#  mnpres     sigp1     sigvm     mxeps     epssh     sigth   impulse    failtm\n")
    erosion_lines.append(f"       0.0{max_princ_stress: .3E}       0.0       0.0       0.0       0.0       0.0          \n")
    erosion_lines.append("$#    idam         -         -         -         -         -         -    lcregd\n")
    erosion_lines.append("                                                                                \n")
    erosion_lines.append("$#   lcfld      nsff   epsthin    engcrt    radcrt   lceps12   lceps13   lcepsmx\n")
    erosion_lines.append("         0                                     0.0                              \n")
    erosion_lines.append("$#  dteflt   volfrac     mxtmp     dtmin\n")
    erosion_lines.append("                                     0.0\n")
    # Add the lines to the list
    list_lines.extend(erosion_lines)

def add_implicit_solver(list_lines: list, dt0: float=0.1):
    """
    Add implicit solver to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param dt0: Initial time step.
    """
    implicit_solver_raw = f"""*CONTROL_IMPLICIT_AUTO
$#   iauto    iteopt    itewin     dtmin     dtmax     dtexp     kfail    kcycle
         1        11         5       0.0       0.0       0.0         0         0
*CONTROL_IMPLICIT_GENERAL
$#  imflag       dt0    imform      nsbs       igs     cnstn      form    zero_v
         1{dt0: 10}         2         1         2         0         0         0
*CONTROL_IMPLICIT_SOLUTION
$#  nsolvr    ilimit    maxref     dctol     ectol     rctol     lstol    abstol
        12        11        15     0.001      0.011.00000E10       0.91.0000E-10
$#   dnorm    diverg     istif   nlprint    nlnorm   d3itctl     cpchk
         2         1         1         0         2         0         0
$#  arcctl    arcdir    arclen    arcmth    arcdmp    arcpsi    arcalf    arctim
         0         0       0.0         1         2       0.0       0.0       0.0
$#   lsmtd     lsdir      irad      srad      awgt      sred
         4         2       0.0       0.0       0.0       0.0"""
    implicit_solver_lines = implicit_solver_raw.split("\n")
    implicit_solver_lines = [line + "\n" for line in implicit_solver_lines]
    list_lines.extend(implicit_solver_lines)

def add_control_timestep(list_lines, dt2ms=-0.01):
    """
    Add control timestep to a .k file, specifically a mass scaling.
    :param list_lines: lines in the key file (see read_keyfile).
    :param dt2ms: Minimum time step. If timestep is under this value, mass scaling will be applied to the concerned elements.
    """
    control_timestep_key = "*CONTROL_TIMESTEP"
    control_timestep_lines = []
    control_timestep_lines.append(f"{control_timestep_key}\n")
    control_timestep_lines.append("$#  dtinit    tssfac      isdo    tslimt     dt2ms      lctm     erode     ms1st\n")
    control_timestep_lines.append(f"       0.0       0.0         0       0.0{dt2ms: .3E}         0         0         0\n")
    # Add the lines to the list
    list_lines.extend(control_timestep_lines)

def add_d3plot(list_lines: list, dt: float=0.1):
    """
    Add d3plot bin out to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param dt: Time step for d3plot results.
    """
    d3plot_key = "*DATABASE_BINARY_D3PLOT"
    d3plot_lines = []
    d3plot_lines.append(f"{d3plot_key}\n")
    d3plot_lines.append("$#      dt      lcdt      beam     npltc    psetid\n")
    d3plot_lines.append(f"{dt: .3E}         0         0         0         0\n")
    # Add extent binary
    extent_binary_key = "*DATABASE_EXTENT_BINARY"
    extent_binary_lines = []
    extent_binary_lines.append(f"{extent_binary_key}\n")
    extent_binary_lines.append("$#   neiph     neips    maxint    strflg    sigflg    epsflg    rltflg    engflg\n")
    extent_binary_lines.append("         0         0         3         1         1         1         1         1\n")
    extent_binary_lines.append("$#  cmpflg    ieverp    beamip     dcomp      shge     stssz    n3thdt   ialemat\n")
    extent_binary_lines.append("         0         0         0         1         1         3         2         1\n")
    extent_binary_lines.append("$# nintsld   pkp_sen      sclp     hydro     msscl     therm    intout    nodout\n")
    extent_binary_lines.append("         0         0       1.0         0         0         0\n")
    extent_binary_lines.append("$#    dtdt    resplt     neipb   quadsld    cubsld   deleres\n")
    extent_binary_lines.append("         0         0                   0         0         0\n")

    # Add elout
    elout_key = "*DATABASE_ELOUT"
    elout_lines = []
    elout_lines.append(f"{elout_key}\n")
    elout_lines.append("$#      dt    binary      lcur     ioopt   option1   option2   option3   option4\n")
    elout_lines.append(f"{dt: .3E}         0         0         1         0         0         0         0\n")

    # Add glstat
    glstat_key = "*DATABASE_GLSTAT"
    glstat_lines = []
    glstat_lines.append(f"{glstat_key}\n")
    glstat_lines.append("$#      dt    binary      lcur     ioopt\n")
    glstat_lines.append(f"{dt: .3E}         0         0         1\n")

    # Add nodout
    nodout_key = "*DATABASE_NODOUT"
    nodout_lines = []
    nodout_lines.append(f"{nodout_key}\n")
    nodout_lines.append("$#      dt    binary      lcur     ioopt   option1   option2\n")
    nodout_lines.append(f"{dt: .3E}         0         0         1       0.0         0\n")

    # Add spcforc
    spcforc_key = "*DATABASE_SPCFORC"
    spcforc_lines = []
    spcforc_lines.append(f"{spcforc_key}\n")
    spcforc_lines.append("$#      dt    binary      lcur     ioopt\n")
    spcforc_lines.append(f"{dt: .3E}         0         0         1\n")

    # Add bndout
    bndout_key = "*DATABASE_BNDOUT"
    bndout_lines = []
    bndout_lines.append(f"{bndout_key}\n")
    bndout_lines.append("$#      dt    binary      lcur     ioopt\n")
    bndout_lines.append(f"{dt: .3E}         0         0         1\n")

    # Add the lines to the list
    list_lines.extend(d3plot_lines)
    list_lines.extend(extent_binary_lines)
    list_lines.extend(elout_lines)
    list_lines.extend(glstat_lines)
    list_lines.extend(nodout_lines)
    list_lines.extend(spcforc_lines)
    list_lines.extend(bndout_lines)

def add_termination(list_lines: list, end_time: float=1.0):
    """
    Add termination to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param end_time: End time of the simulation.
    """
    termination_key = "*CONTROL_TERMINATION"
    termination_lines = []
    termination_lines.append(f"{termination_key}\n")
    termination_lines.append("$#  endtim    endcyc     dtmin    endeng    endmas     nosol\n")
    termination_lines.append(f"{end_time: .3E}         0       0.0       0.01.000000E8         0\n")
    # Add the lines to the list
    list_lines.extend(termination_lines)


def modify_node_coordinates(list_lines: list, nodes_dict: dict) -> None:
    """
    Modify node coordinates in a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param nodes_dict: Dictionary of nodes coordinates {node_id: [x, y, z]}.
    """
    node_key = "*NODE"
    # Modify the part
    i = 0
    while i < len(list_lines):
        if list_lines[i].startswith(node_key):
            i += 1
            while not list_lines[i].startswith("*"):
                try:
                    node_id = int(list_lines[i][:8])
                    if node_id in nodes_dict.keys():
                        list_lines[i] = f"{node_id: 8}{nodes_dict[node_id][0]: .9e}{nodes_dict[node_id][1]: .9e}{nodes_dict[node_id][2]: .9e}\n"
                    i += 1
                except ValueError:
                    i += 1
                    continue
        i += 1

def add_hourglass_energy(list_lines: list) -> None:
    """
    Add hourglass energy computation to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    """
    hourglass_key = "*CONTROL_ENERGY"
    hourglass_lines = []
    hourglass_lines.append(f"{hourglass_key}\n")
    hourglass_lines.append("$#    hgen      rwen    slnten     rylen     irgen     maten     drlen     disen\n")
    hourglass_lines.append("         2         2         1         1         2         1         1         1\n")
    # Add the lines to the list
    list_lines.extend(hourglass_lines)

def add_part(list_lines: list, name: str=None) -> int:
    """
    Add part to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param name: Name of the part.
    """
    part_key = "*PART"
    part_lines = []
    part_lines.append(f"{part_key}\n")
    part_lines.append("$#                                                                         title\n")
    part_ids = rk.get_ids(part_key, list_lines)
    part_id = max(part_ids) + 1 if part_ids else 1
    part_lines.append(f"{name}\n")
    part_lines.append("$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid\n")
    part_lines.append("         1         0         0         0         0         0         0         0\n")
    # Add the lines to the list
    list_lines.extend(part_lines)
    return part_id

def add_nodes(list_lines: list, nodes: np.ndarray) -> None:
    """
    Add nodes to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param nodes: Nodes coordinates [[node_id, x, y, z]].
    """
    node_key = "*NODE"
    node_lines = []
    node_lines.append(f"{node_key}\n")
    node_lines.append("$#   nid               x               y               z      tc      rc\n")
    for node in nodes:
        node_lines.append(f"{int(node[0]): 8}{node[1]: .9e}{node[2]: .9e}{node[3]: .9e}       0       0\n")
    # Add the lines to the list
    list_lines.extend(node_lines)

def add_element_solids(list_lines: list, part_id: int, elements: np.ndarray) -> None:
    """
    Add element solids to a .k file.
    :param list_lines: lines in the key file (see read_keyfile).
    :param part_id: Part id.
    :param elements: Elements [[element_id, node1, node2, node3, node4, ...]].
    """
    if len(elements[0][1:]) in [4, 8]:
        element_key = "*ELEMENT_SOLID"
        element_lines = []
        element_lines.append(f"{element_key}\n")
        element_lines.append("$#   eid      pid      n1      n2      n3      n4      n5      n6      n7      n8\n")
        if len(elements[0][1:]) == 4:
            for element in elements:
                element_lines.append(f"{element[0]: 8}{part_id: 8}{element[1]: 8}{element[2]: 8}{element[3]: 8}{element[4]: 8}{element[4]: 8}{element[4]: 8}{element[4]: 8}{element[4]: 8}\n")
        if len(elements[0][1:]) == 8:
            for element in elements:
                element_lines.append(f"{element[0]: 8}{part_id: 8}{element[1]: 8}{element[2]: 8}{element[3]: 8}{element[4]: 8}{element[5]: 8}{element[6]: 8}{element[7]: 8}{element[8]: 8}\n")



    elif len(elements[0][1:]) in [10]:
        element_key = "*ELEMENT_SOLID (ten nodes format)"
        element_lines = []
        element_lines.append(f"{element_key}\n")
        for element in elements[:1]:
            element_lines.append("$#   eid      pid\n")
            element_lines.append(f"{element[0]: 8}{part_id: 8}\n")
            element_lines.append("$#    n1      n2      n3      n4      n5      n6      n7      n8      n9     n10\n")
            element_lines.append(f"{element[1]: 8}{element[2]: 8}{element[3]: 8}{element[4]: 8}{element[5]: 8}{element[6]: 8}{element[7]: 8}{element[8]: 8}{element[9]: 8}{element[10]: 8}\n")
        for element in elements[1:]:
            element_lines.append(f"{element[0]: 8}{part_id: 8}\n")
            element_lines.append(f"{element[1]: 8}{element[2]: 8}{element[3]: 8}{element[4]: 8}{element[5]: 8}{element[6]: 8}{element[7]: 8}{element[8]: 8}{element[9]: 8}{element[10]: 8}\n")

    # Add the lines to the list
    list_lines.extend(element_lines)