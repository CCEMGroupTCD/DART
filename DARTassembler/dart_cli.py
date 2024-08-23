import argparse
from DARTassembler import filter_ligands, assemble_complexes, save_dbinfo, concatenate_ligand_databases, run_installation_test, get_default_config_files_saved

init_cli_output = r"""
================================================================================
                            ____  ___    ____  ______
                           / __ \/   |  / __ \/_  __/
                          / / / / /| | / /_/ / / /   
                         / /_/ / ___ |/ _, _/ / /    
                        /_____/_/  |_/_/ |_| /_/     
        
          DART - Directed Assembly of Random Transition metal complexes
================================================================================
"""


modules = ['ligandfilters', 'assembler', 'dbinfo', 'concat', 'test', 'configs']

def check_n_args(args, n):
    if len(args) != n:
        raise ValueError(f'Expected {n} path, got {len(args)} arguments.')

def main():
    desc = f"""DART command-line interface for assembling novel transition metal complexes from a database of ligands. Available modules: {", ".join(modules)}.
Usage: dart <module> --path <path>
"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('module', choices=modules, help='DART module that you want to use')
    parser.add_argument('--path', required=True, help='Path to the input file(s)', nargs='*')

    args = parser.parse_args()

    print(init_cli_output)
    module_title = f'  Execute module: {args.module}  '
    print(f'{module_title:#^80}')
    if args.path:
        print(f'Input file: {args.path}')

    if args.module == 'ligandfilters':
        check_n_args(args.path, 1)
        filter_ligands(args.path[0])
    elif args.module == 'assembler':
        check_n_args(args.path, 1)
        assemble_complexes(args.path[0])
    elif args.module == 'dbinfo':
        check_n_args(args.path, 1)
        save_dbinfo(args.path[0])
    elif args.module == 'concat':
        concatenate_ligand_databases(args.path)
    elif args.module == 'test':
        if len(args.path) == 0:
            path = None
        else:
            check_n_args(args.path, 1)
            path = args.path[0]
        run_installation_test(path)
    elif args.module == 'configs':
        check_n_args(args.path, 1)
        get_default_config_files_saved(args.path[0])
    else:
        raise ValueError(f'Unknown module {args.module}.')

if __name__ == '__main__':
    main()
