"""
Integration test for outputting a csv file of the ligand database.
"""
import shutil

from DARTassembler.dbinfo import dbinfo
from DARTassembler.src.constants.Paths import project_path
from pathlib import Path


def test_make_ligand_db_csv(nmax=1000):
    output_path = project_path().extend('testing', 'integration_tests', 'dbinfo', 'data_output', 'MetaLig_v1.7.csv')

    # Delete output directory so that the test detects if files are not written.
    shutil.rmtree(output_path.parent, ignore_errors=True)

    db = dbinfo(input_path='metalig', output_path=output_path, nmax=nmax)

    #%% ==============    Doublecheck refactoring    ==================
    from dev.test.Integration_Test import IntegrationTest
    old_dir = Path(str(output_path).replace('/data_output/', '/benchmark_data_output/'))
    if old_dir.exists():
        test = IntegrationTest(new_dir=output_path.parent, old_dir=old_dir.parent)
        test.compare_all()
        print('Test for dbinfo passed!')
    else:
        print(f'ATTENTION: could not find benchmark folder "{old_dir}"!')

    return db


if __name__ == "__main__":
    nmax = 1000

    db = test_make_ligand_db_csv(nmax=nmax)

