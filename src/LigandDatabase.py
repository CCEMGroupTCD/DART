import json
import time

from joblib import Parallel, delayed
from src.read_database import read_local_tmqm_db
from src.Extracted_Molecule import Extracted_Molecule
from src.Molecule import RCA_Molecule, RCA_Ligand
from src.utilities import coordinates_to_xyz_str, flatten_list
from src.constants import get_monodentate_list
from mendeleev import element
import pickle
from tqdm import tqdm
from ase import io
import numpy as np
import pandas as pd
from src.MoleculeDatabase import MoleculeDatabase
import itertools
from copy import deepcopy
from pathlib import Path

def call_method_on_object(obj, method: str):
    x = getattr(obj, method)
    result = x()
    return x

def group_list_without_hashing(ligand_list: list) -> list:
    """
    Returns a list of list with unique elements grouped together. Works without hashing, just using equity.
    :param ligand_list: list of elements
    :return: list of lists of grouped elements
    """
    groupings = {}
    counter = 0
    for lig1 in ligand_list:
        
        tmp_groupings = {}
        equal = False
        
        for i, lig_list in groupings.items():
            lig_representative = lig_list[0]
            equal = lig_representative == lig1
            
            if equal:
                
                if i in tmp_groupings:
                    tmp_groupings[i].append(lig1)
                else:
                    tmp_groupings[i] = lig1
                    
                break
                
        if not equal:
            tmp_groupings[counter] = [lig1]
            counter += 1
        
        for i in tmp_groupings.keys():
            
            if i in groupings:
                groupings[i].append(tmp_groupings[i])
            else:
                groupings[i] = tmp_groupings[i]
    
    groupings = [group for group in groupings.values()]
    return groupings
def get_unique_elements_of_list_without_hashing(ligand_list: list) -> list:
    """
    Returns unique elements in the input list without hashing, just using equity.
    :param ligand_list: list of elements
    :return: list of unique elements
    """
    unique_hash_ligand_list = []
    for lig1 in ligand_list:
        
        if unique_hash_ligand_list == []:
            unique_hash_ligand_list.append(lig1)
        
        else:
            new = []
            for lig2 in unique_hash_ligand_list:
                different = lig2 != lig1
                new.append(different)
            
            if all(new):
                unique_hash_ligand_list.append(lig1)
        
    return unique_hash_ligand_list

def get_all_ligands_by_hashes(unique_hashed_ligands: list, all_ligands: list) -> dict:
    """
    Get dictionary of hashes with list of ligands with this hash
    :param unique_hashed_ligands: list of ligands with unique hashes.
    :param all_ligands: list of all ligands with hashes
    :return: dictionary of hash: list_of_ligands
    """
    all_hashes = [ligand.graph_hash for ligand in unique_hashed_ligands]
    all_ligands_by_hashes = {h: [] for h in all_hashes}
    for ligand in all_ligands:
        all_ligands_by_hashes[ligand.graph_hash].append(ligand)
    
    return all_ligands_by_hashes

def iter_over_ligand_dict(ligand_dict: dict, return_denticity: bool=False) -> RCA_Ligand:
    for denticity, ligand_list in ligand_dict.items():
        for ligand in ligand_list:
            if return_denticity:
                yield ligand, denticity
            else:
                yield ligand
def total_number_of_ligands(ligand_dict: dict) -> int:
    num = 0
    for denticity, ligand_list in ligand_dict.items():
        num += len(ligand_list)
    return num

class LigandDatabase(MoleculeDatabase):

    def __init__(self, data_path, id_col, TestSize=False):
        MoleculeDatabase.__init__(self, data_path=data_path, id_col=id_col, TestSize=TestSize)

        self.full_ligand_dict = {}
        self.ligand_dict = {}

        self.extraction_error_count = 0

        # exclusively for later filter stages
        self.filtered_database_dict = None
        self.filtered_database = None
        
        self.ligand_db_output_data_path = Path(self.output_data_path, 'LigandDatabases')
        self.default_all_Extracted_Molecules_json_path = Path(self.ligand_db_output_data_path, 'all_Extracted_Molecules.json')
        self.save_tmp_pickles_path = Path(self.ligand_db_output_data_path)

    def __len__(self):
            """
            returns total length of the ligand_dict
            """
            if self.ligand_dict == {}:
                return 0
            else:
                len_ = 0
                for key, _list in self.ligand_dict.items():
                    len_ += len(_list)
                return len_

    def __str__(self):
        if self.ligand_dict == {}:
            return ""
        else:
            str_ = ""
            for key, _list in self.ligand_dict.items():
                str_ += f"For denticiy {key} we have {len(_list)} ligands\n"
            return str_

    def get_information(self):
        print(str(self))

    @staticmethod
    def read_db():
        """
        # todo: this should be generalized to a more customizable input system
        return: dict of the type {csd_code: coordinates}
        """
        return read_local_tmqm_db()

    # def get_molecule_lookup_dict(self, path: str = "../data"):
    #     """
    #     for the remainder we only have the extracted ligands from the molecules in the database
    #     if we would like to have a lookup table, call this method
    #     :path: where to store the lookup table
    #     """
    #     dict_ = {}
    #     for csd_key, coordinates in tqdm(self.extracted_information.items()):
    #         with open("../tmp/tmp.xyz", "w+") as text_file:
    #             text_file.write(coordinates_to_xyz_str(coordinates=coordinates))
    #         dict_[csd_key] = RCA_Molecule(io.read("../tmp/tmp.xyz"))
    #
    #     with open(f"{path}/csd_molecule_lookup_file.pickle", "wb") as h:
    #         pickle.dump(dict_, h)
    def extract_ligands_of_one_complex(self, csd_code, molecule, metals_of_interest, denticity_numbers_of_interest):
        ligands = []
        try:
            if metals_of_interest is None or element(int(molecule.original_metal)).symbol in metals_of_interest:
                # now we extract the ligands of the desired molecule
                molecule.extract_ligands(denticity_numbers=denticity_numbers_of_interest)

                # and add the ligands to our dict, if there are any
                for lig in molecule.ligands:
                    if lig.denticity in self.full_ligand_dict.keys():
                        ligands.append({
                                            'csd_code': csd_code,
                                            'ligand': lig,
                                            'denticity': lig.denticity,
                                            'error': None
                        })
                        # self.full_ligand_dict[lig.denticity].append(lig)
                    else:
                        ligands.append({
                                                'csd_code': csd_code,
                                                'ligand': None,
                                                'denticity': None,
                                                'error': None
                        })

        except Exception as ex:
            print(f"An Error occured: {ex}")
            ligands.append({
                                'csd_code': csd_code,
                                'ligand': None,
                                'denticity': None,
                                'error': str(ex)
            })
            # self.extraction_error_count += 1
            # self.extraction_errors[csd_code] = str(ex)
            # pass
        
        return ligands
    
    def extract_ligands(self, denticity_numbers_of_interest, metals_of_interest=None, n_jobs=1):
        
        if isinstance(metals_of_interest, str):
            metals_of_interest = [metals_of_interest]

        if isinstance(denticity_numbers_of_interest, int):
            denticity_numbers_of_interest = [denticity_numbers_of_interest]

        #
        # init empty dict
        self.full_ligand_dict = {dent: [] for dent in denticity_numbers_of_interest}
        self.get_all_Extracted_Molecules()
        
        ligands_list = Parallel(n_jobs=n_jobs)(delayed(
                                                            self.extract_ligands_of_one_complex)
                                                            (csd_code, molecule, metals_of_interest, denticity_numbers_of_interest)
                                                            for csd_code, molecule in tqdm(self.all_Extracted_Molecules.items(), desc='Extracting ligands')
                                                    )

        ligands_list = flatten_list(ligands_list)
        for d in ligands_list:
            denticity = d['denticity']
            ligand = d['ligand']
            csd_code = d['csd_code']
            error = d['error']
            
            if not ligand is None:
                assert not denticity is None
                self.full_ligand_dict[denticity].append(ligand)
                
            if not error is None:
                self.extraction_error_count += 1
                self.extraction_errors[csd_code] = error

        print(f"Extraction complete -- number of errors {self.extraction_error_count}")

    def extract_ligands_old(self, denticity_numbers_of_interest, metals_of_interest=None):
    
        if isinstance(metals_of_interest, str):
            metals_of_interest = [metals_of_interest]
    
        if isinstance(denticity_numbers_of_interest, int):
            denticity_numbers_of_interest = [denticity_numbers_of_interest]
    
        #
        # init empty dict
        self.full_ligand_dict = {dent: [] for dent in denticity_numbers_of_interest}
        self.get_all_Extracted_Molecules()
    
        for csd_code, molecule in tqdm(self.all_Extracted_Molecules.items(), desc='Extracting ligands'):
            try:
                if metals_of_interest is None or element(int(molecule.original_metal)).symbol in metals_of_interest:
                    # now we extract the ligands of the desired molecule
                    molecule.extract_ligands(denticity_numbers=denticity_numbers_of_interest)
                
                    # and add the ligands to our dict, if there are any
                    for lig in molecule.ligands:
                        if lig.denticity in self.full_ligand_dict.keys():
                            self.full_ligand_dict[lig.denticity].append(lig)
        
            except Exception as ex:
                print(f"An Error occured: {ex}")
                self.extraction_error_count += 1
                self.extraction_errors[csd_code] = str(ex)
                pass
    
        print(f"Extraction complete -- number of errors {self.extraction_error_count}")
    def add_monodentate_ligands(self):
        """
        problem is that we don't extract monodentates; so we just insert them customly from pre-defined constants
        """
        self.ligand_dict[1] = get_monodentate_list()
    
    def get_all_denticities(self, ligand_dict):
        denticities = [denticity for denticity in ligand_dict.keys()]
        return denticities
    
    def save_self_as_pickle(self, outpath):
        with open(outpath, 'wb') as f:
            pickle.dump(self, f)
        return
    
    def filter_duplicates(self, n_jobs: int):
        print('Start filtering duplicates.')
        all_ligands = list(iter_over_ligand_dict(self.full_ligand_dict))
        
        self.save_self_as_pickle(Path(self.save_tmp_pickles_path, 'lg_before_graph_hashes.pkl'))
        # Calculate graphs and graph_hashes for all ligands and save as attribute.
        all_graph_hashes = Parallel(n_jobs=n_jobs)(delayed(
                                                    call_method_on_object)(lig, 'get_graph_hash')   # same as: lambda lig: lig.get_graph_hash())(lig)
                                                    for lig in tqdm(all_ligands, desc='Get graph hashs')
                                                   )
        self.save_self_as_pickle(Path(self.save_tmp_pickles_path, 'lg_after_graph_hashes.pkl'))
        
        
        
        
        
        unique_hashed_ligands = list(set(all_ligands))
        print(f'Number of unique hashed ligands: {len(unique_hashed_ligands)}.')
        self.save_self_as_pickle(Path(self.save_tmp_pickles_path, 'lg_after_unique_hashed_ligands.pkl'))
        
        all_hashes = [lig.hash for lig in unique_hashed_ligands]
        all_graph_hashes = [lig.graph_hash for lig in unique_hashed_ligands]
        all_names = [lig.name for lig in unique_hashed_ligands]
        df = pd.DataFrame(np.array([all_names, all_hashes, all_graph_hashes]).T, columns=['name', 'hash', 'graph_hash'])
        df['gh_unique'] = df['graph_hash'].duplicated()
        df['h_unique'] = df['hash'].duplicated()
        print(f'Percentage of duplicates: {100*sum(df["gh_unique"])/len(df)}')
        
        # For all ligands with same graph hash, find unique ligands by equity comparison.
        all_ligands_by_hashes = get_all_ligands_by_hashes(unique_hashed_ligands, all_ligands)
        grouped_unique_ligands = []
        for graph_hash, ligand_list in tqdm(all_ligands_by_hashes.items(), desc='Compare graphs exact'):
            unique_hash_ligand_list = group_list_without_hashing(ligand_list)
            grouped_unique_ligands.extend(unique_hash_ligand_list)
        self.save_self_as_pickle(Path(self.save_tmp_pickles_path, 'lg_after_equality_comparison.pkl'))
        
        unique_ligands = []
        for same_ligands in grouped_unique_ligands:
            
            unique_ligand = same_ligands[0]
            unique_ligand_name = 'unq_' + unique_ligand.name
            unique_ligands.append(unique_ligand)
            
            for ligand in same_ligands:
                ligand.unique_name = unique_ligand_name
                
                check_props = ['denticity', 'graph_hash', 'hash']
                for prop in check_props:
                    if getattr(unique_ligand, prop) != getattr(ligand, prop):
                        print(f'WARNING: Different {prop} for unique ligand {unique_ligand.name} ({getattr(unique_ligand, prop)}) and ligand {ligand.name} ({getattr(ligand, prop)}).')
                
        
        # Get unique ligand dictionary with denticity as output format.
        self.unique_ligand_dict = {denticity: [] for denticity in self.get_all_denticities(self.full_ligand_dict)}
        for unique_ligand in unique_ligands:
            self.unique_ligand_dict[unique_ligand.denticity].append(unique_ligand)
            
        print(f'Number of unique ligands: {len(unique_ligands)}.')
        return self.unique_ligand_dict
    
    def get_df_of_all_ligands(self):
        """
        Returns a dataframe with name, denticity, CSD code and type of every ligand in the database.
        """
        ligand_props = []
        for ligand_list in self.full_ligand_dict.values():
            for l in ligand_list:
                ligand_props.append({
                    'name': l.name,
                    'unique_name': l.unique_name,
                    'csd_code': l.csd_code if hasattr(l, 'csd_code') else np.nan,
                    'original_metal_symbol': l.original_metal_symbol if hasattr(l, 'original_metal_symbol') else np.nan,
                    'denticity': l.denticity,
                    'graph_hash': l.graph_hash,
                    'coordinates': str(l.coordinates),
                    'atomic_props': str(l.atomic_props),
                    #'hash': l.hash # makes issues in pd.testing.assert_frame_equal, probably because of overflow
                    })
        df = pd.DataFrame(ligand_props)
        return df
    
    def get_dict_of_all_Extracted_Molecules(self):
        d = {}
        for mol_id, mol in self.all_Extracted_Molecules.items():
            d[mol_id] = mol.complete.global_props
            d[mol_id]['ligands'] = []
            for lig in mol.ligands:
                lig_dict = {}
                lig_dict['atomic_props'] = lig.atomic_props
                lig_dict['coordinates'] = lig.coordinates
                lig_dict['denticity'] = lig.denticity
                lig_dict['name'] = lig.name
                lig_dict['unique_name'] = lig.unique_name
                d[mol_id]['ligands'].append(lig_dict)
        
        self.Extracted_Molecules_dict = d
        return self.Extracted_Molecules_dict
        
    def run_sanity_checks_for_all_Extracted_Molecules(self) -> bool:
        """
        Run a lot of sanity checks.
        :return: True if all sanity checks were correct else False.
        """
        all_mol_ids = []
        for mol_id, mol in tqdm(self.all_Extracted_Molecules.items(), desc='Checking molecules'):
            assert not mol_id in all_mol_ids, '{mol_id}: Mol ID is not unique.'
            all_mol_ids.append(mol_id)
            
            mol.run_sanity_checks(mol_id)
        
        return
    
    def save_Extracted_Molecules_to_json(self, outpath: str=None):
        print('Start saving all_Extracted_Molecules to json.')
        
        extracted_molecules_dict = self.get_dict_of_all_Extracted_Molecules()
        
        outpath = outpath or self.default_all_Extracted_Molecules_json_path
        with open(outpath, 'w') as file:
            json.dump(extracted_molecules_dict, file)
        
        print(f'Saved all_Extracted_Molecules to {outpath}')
        
        return

if __name__ == '__main__':
    
    # test_lists = [
    #     [1, 2, 3, 3, 2],
    #     [5, 5, 5],
    #     [1, 2, 3, 4],
    #     [[1], [2], [2], [4], [1]]
    # ]
    # for test_list in test_lists:
    #     grouping = group_list_without_hashing(test_list)
    #     pass
    
    ligand_db_file = "../data/LigandDatabases/ligand_db_test.pickle"
    
    with open(ligand_db_file, 'rb') as file:
        ligand_db = pickle.load(file)
        print('Loaded ligand db from pickle.')

    ligand_db.run_sanity_checks_for_all_Extracted_Molecules()
    
    # ligand_db.save_Extracted_Molecules_to_json()
    
    # ligand_db.filter_duplicates()
    #
    # n_unique_ligands = total_number_of_ligands(ligand_db.unique_ligand_dict)
    # n_total_ligands = total_number_of_ligands(ligand_db.full_ligand_dict)
    # print(f'There are {n_unique_ligands} unique ligands out of a total of {n_total_ligands} ligands.')
    


