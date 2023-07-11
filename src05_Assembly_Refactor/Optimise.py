from building_block_utility import mercury_remover
from constants.Paths import project_path
from openbabel import openbabel as ob
from rdkit.Chem import rdmolfiles
from pathlib import Path
import numpy as np
import warnings
import shutil
from copy import deepcopy
import re
# from test.profiling import profile as line_profile
# from test.profiling import print_stats
from line_profiler_pycharm import profile as line_profile

from src01.utilities_Molecule import get_coordinates_and_elements_from_OpenBabel_mol, get_concatenated_xyz_string_from_coordinates


class OPTIMISE:
    def __init__(self, isomer, ligand_list, building_blocks, instruction):
        self.isomer = isomer
        self.ligands = ligand_list
        self.building_blocks = building_blocks
        self.instruction = instruction

    def concatenate_files(self, file1_path, file2_path, output_path):
        """
        Concatenates the contents of two input files into a new output file. Supports if the output path is the same as one of the input paths.

        Args:
            file1_path (str or pathlib.Path): The path to the first input file.
            file2_path (str or pathlib.Path): The path to the second input file.
            output_path (str or pathlib.Path): The path to the output file.
        """
        # Read in the contents of both input files
        with open(file1_path, 'r') as f_in:
            file1_contents = f_in.read()
        with open(file2_path, 'r') as f_in:
            file2_contents = f_in.read()

        # Write the contents to the output file, with a blank line separating them
        with open(output_path, 'w') as f_out:
            f_out.write(file1_contents)
            f_out.write(file2_contents)

        return


    def movie(self, coord_list: list[np.array], element_list: list[list[str]]) -> None:
        """
        Saves a movie of the optimization process. The movie is saved as a concatenated .xyz file.
        """
        xzy_string = get_concatenated_xyz_string_from_coordinates(coord_list, element_list=element_list)
        with open(str(project_path().extend("tmp", "opt_movie.xyz")), "a") as f:
            f.write(xzy_string)

        return
    def Optimise_STK_Constructed_Molecule(self, nsteps: int=50):
        # print("1 " + str(type(self.isomer)))
        if self.isomer is None:
            warnings.warn("!!!Warning!!! -> None detect in optimiser -> Returning None")
            return [None, None]
        elif self.instruction == "False":
            return [self.isomer, self.building_blocks]

        else:
            print("Beginning Optimisation")
            # print("2 " + str(type(self.isomer)))
            debug = True       # TODO True
            # todo: Return the rotated stk building blocks as well, they may still be of use to someone
            # REFERENCE: https://github.com/hjkgrp/molSimplify/blob/c3776d0309b5757d5d593e42db411a251b558e59/molSimplify/Scripts/structgen.py#L658
            # REFERENCE: https://gist.github.com/andersx/7784817

            # stk to xyz string
            complex_mol = self.isomer.to_rdkit_mol()
            xyz_string = rdmolfiles.MolToXYZBlock(complex_mol)

            # setup conversion
            conv = ob.OBConversion()
            conv.SetInAndOutFormats('xyz', 'xyz')
            mol = ob.OBMol()
            conv.ReadString(mol, xyz_string)

            # Define constraints
            # OPEN BABEL INDEXING SARTS AT ONE !!!!!!!!!!!!!!!!!!!!!!!!!!!
            constraints = ob.OBFFConstraints()
            constraints.AddAtomConstraint(1)  # Here we lock the metal

            # we constrain the all the coordinating atoms to the metal
            sum_of_atoms = []
            for ligand in self.ligands.values():
                coord_indexes = ligand.ligand_to_metal
                for atom_index in coord_indexes:
                    # constraints.AddAtomConstraint(1 + 1 + atom_index + sum(sum_of_atoms))
                    constraints.AddAtomConstraint(1 + 1 + atom_index + sum(sum_of_atoms))  # The one is to account for open babel indexing starting at 1 and to account for the metal
                    assert (1 + 1 + atom_index + sum(sum_of_atoms)) <= int(xyz_string.split("\n")[0])
                # this is so we don't take into account any mercury that might be in the atomic props (really only an issue for tetradentate non-planar ligands.py as they make use of the add atom function)
                sum_of_atoms.append(len([i for i in ligand.atomic_props["atoms"] if i != "Hg"]))

            # Set up the force field with the constraints
            forcefield = ob.OBForceField.FindForceField("Uff")
            forcefield.Setup(mol, constraints)
            forcefield.SetConstraints(constraints)


            # Optimize the molecule coordinates using the force field with constrained atoms.
            optimized_coords = []
            optimized_elements = []
            forcefield.ConjugateGradientsInitialize(nsteps)
            while forcefield.ConjugateGradientsTakeNSteps(1):
                if debug:
                    forcefield.GetCoordinates(mol)
                    coords, elements = get_coordinates_and_elements_from_OpenBabel_mol(mol)
                    optimized_coords.append(coords)
                    optimized_elements.append(elements)
            if debug:
                self.movie(coord_list=optimized_coords, element_list=optimized_elements)
            forcefield.GetCoordinates(mol)





            # # Do a 50 steps conjugate gradient minimization
            # # and save the coordinates to mol.
            # # The below function is very slow -> better off just setting i = 200 if you are not debugging
            # # it is worth nothing that the final coordinates of an optimised molecule will be slightly different
            # # depending on whether or not debug is set to true or false. This is an important point especially for unit testing
            # if debug:
            #     for i in range(nsteps):
            #         forcefield.ConjugateGradients(i)
            #         forcefield.GetCoordinates(mol)
            #         conv.WriteFile(mol, str(project_path().extend("tmp", "opt_in_xyz.xyz")))
            #         self.movie(coord_list=None, element_list=None)
            #
            # elif not debug:
            #     forcefield.ConjugateGradients(nsteps)
            #     forcefield.GetCoordinates(mol)


            # UPDATE THE COORDINATES OF THE STK BUILDING BLOCK ISOMER WITH THE NEW COORDINATES
            xyz_string_output = conv.WriteString(mol)
            list_of_nums = re.findall(r"[-+]?(?:\d*\.*\d+)", f"Current Level: {xyz_string_output}")
            num_of_atoms = int(list_of_nums[0])
            del list_of_nums[0]  # we remove the number that corresponds to the number of atoms
            i = 0
            new_position_matrix = []
            for coord in range(num_of_atoms):
                new_position_matrix.append([float(list_of_nums[0 + i]), float(list_of_nums[1 + i]), float(list_of_nums[2 + i])])
                i += 3
            new_position_matrix = np.array(new_position_matrix)
            self.isomer = self.isomer.with_position_matrix(new_position_matrix)
            # print("3 "+str(type(self.isomer)))
            #
            #
            # UPDATE THE COORDINATES OF THE STK BUILDING BLOCK WITH THE NEW COORDINATES
            i = 0
            num_of_lig_atoms = []
            for bb in self.building_blocks.values():
                bb = mercury_remover(bb)
                pos_matrix = bb.get_position_matrix()
                # print(pos_matrix)
                for atom in range(bb.get_num_atoms()):
                    pos_matrix[atom] = new_position_matrix[atom + 1 + sum(num_of_lig_atoms)]
                num_of_lig_atoms.append(bb.get_num_atoms())
                bb = bb.with_position_matrix(pos_matrix)
                self.building_blocks[i] = bb
                i += 1
        return [self.isomer, self.building_blocks]

    def touch_file(self, file_path: str):
        # Convert the file path to a Path object
        file_path = Path(file_path)
        # Touch the file by setting its modification time to the current time
        file_path.touch()
