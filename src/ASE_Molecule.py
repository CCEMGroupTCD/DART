import numpy as np
from ase import io, Atoms, neighborlist
from ase.visualize import view
import matplotlib.pyplot as plt
import networkx as nx
from sympy import Point3D, Plane


class ASE_Molecule:
    '''
    just a ase molecule, but extended by some custom functions
    '''

    def __init__(self, mol):
        '''
        :param mol: ASE Molecule
        '''
        self.mol = mol

    def view_graph(self):
        cutOff = neighborlist.natural_cutoffs(self.mol)
        neighborList = neighborlist.NeighborList(cutOff, self_interaction=False, bothways=True)
        neighborList.update(self.mol)
        graph = neighborList.get_connectivity_matrix(sparse=False)
        labels = {i: el for i, el in enumerate(self.mol.get_chemical_symbols())}
        rows, cols = np.where(graph == 1)
        edges = zip(rows.tolist(), cols.tolist())
        gr = nx.Graph()
        gr.add_edges_from(edges)
        nx.draw_networkx(gr, node_size=500, with_labels=True, labels=labels)
        plt.show()

    def view_3d(self):
        view(self.mol)


class xyz_file:

    def __init__(self, atom_number: int, coordinates: dict, csd_code: str):
        self.total_atom_number = atom_number
        self.coordinates = coordinates
        # {number in xyz_file:[Name von Atom, Coordinaten als np.array]
        self.csd_code = csd_code

    def get_xyz_file_format_string(self):
        str_ = f"{self.total_atom_number}\n \n"
        for coord in self.coordinates.values():
            str_ += f"{coord[0]} \t {coord[1][0]} \t {coord[1][1]} \t {coord[1][2]} \n"

        return str_

    def xyz_to_ASE(self):
        with open("../tmp/tmp.xyz", "w+") as text_file:
            text_file.write(self.get_xyz_file_format_string())

        return ASE_Molecule(io.read("../tmp/tmp.xyz"))


class ASE_Ligand(ASE_Molecule):
        '''
        inherits its methods from ASE Molecule, while needs some extra information
        '''

        def __init__(self, xyz: xyz_file, property_dict: dict):
            super().__init__(Atoms([coord[0] for coord in xyz.coordinates.values()],
                                   positions=[coord[1] for coord in xyz.coordinates.values()]))

            self.denticity = property_dict['denticity']
            self.ligand_to_metal = property_dict['ligand_to_metal']
            self.csd_code = xyz.csd_code
            self.original_metal = property_dict['original_metal']
            self.xyz = xyz
            self.name = property_dict['name']

            # todo: Braucht noch ein bisschen testing
            self.type = self.get_type()

        def get_assembly_dict(self):
            """
            only to get the attributes required for the assembly with cians script a little faster
            :return: {index: list, type: list, xyz_str: str}
            """
            dict_ = {}

            dict_["index"] = [i for i, el in enumerate(self.ligand_to_metal) if el == 1]
            dict_["type"] = [self.xyz.coordinates[i][0] for i in dict_["index"]]
            dict_["str"] = self.xyz.get_xyz_file_format_string()

            return dict_

        def get_type(self):
            if self.denticity == 2:
                return 'p'
            elif self.denticity == 5:
                return 'np'
            else:
                if self.check_if_planar() is True:
                    return 'p'
                else:
                    return 'np'

        def check_if_planar(self, eps=1):
            """
            :param lig:
            :param eps: durch try'n'error obtained
            eps für (d=4) -> 1
            :return:
            """
            fc = list()

            for index, information in self.xyz.coordinates.items():
                if self.ligand_to_metal[index] == 1:
                    fc.append(information[1])

            assert len(fc) == self.denticity

            if self.denticity == 3:
                c1, c2, c3 = Point3D(fc[0]), Point3D(fc[1]), Point3D(fc[2])
                E = Plane(c1, c2, 0)
                if E.distance(c3) < eps:
                    return True

            if self.denticity == 4:
                c1, c2, c3, c4 = Point3D(fc[0]), Point3D(fc[1]), Point3D(fc[2]), Point3D(fc[3])
                E = Plane(c1, c2, c3)
                if E.distance(c4) < eps:
                    return True

            return False


#
# das ist zu einfach und es fehlt irgendwie auch coordination. Ist irgendwie mist
def merge(ligA: ASE_Ligand, ligB: ASE_Ligand):

    properties = dict()

    properties['denticity'] = ligA.denticity + ligB.denticity
    properties['ligand_to_metal'] = ligA.ligand_to_metal + ligB.ligand_to_metal
    if ligA.original_metal == ligB.original_metal:
        properties['original_metal'] = ligA.original_metal
    else:
        properties['original_metal'] = "None"

    properties["name"] = ligA.name + ligB.name

    #
    new_atom_number = ligA.xyz.total_atom_number + ligB.xyz.total_atom_number
    new_coordinates = ligA.xyz.coordinates.copy()
    n = len(ligA.xyz.coordinates)

    for number, coord_list in ligB.xyz.coordinates.items():
        new_coordinates[number+n] = coord_list

    new_xyz = xyz_file(atom_number=new_atom_number,
                       csd_code="None",
                       coordinates=new_coordinates
                       )

    return ASE_Ligand(property_dict=properties, xyz=new_xyz)

