# A general script to create parameter configurations for GPUPeasy.
#
# This grid off-loads the parameter configurations to a grid-config class
# and works as long as this class is configured correctly.
#
# Usage:
#   python gridgen.py GRIDCONFIG.py PROJ_NAME ACTION
#
# We support 3 actions:
#
# build: Create the folders for jobs and peasy scripts for it.
# clean: Remove a project
#   - Removes scripts
#   - Removes dump folder
# cbuild: clean and build.

import itertools
import os
import shutil
import pandas as pd
import argparse
from gridgenerator.utils import CLog as lg


class ValidGridGenerator():

    def __init__(self, job_name, cfg):
        '''
        Does a bunch of checks for grid search and generates a gpu-peasy file
        containing valid grid points only.

        Not the most beautiful peace of system.
        '''
        self.job_name = job_name
        self.cfg = cfg

    def __get_valid_outdir__(self):
        '''
        Assumes peasy jobs go into:
            top-directory/peasy_projname/job_id/

        Make sure that the top-directory directory already exists. We dont
        create these. If it exists, assert that peasy_projname is empty if it
        exists. If it does not exist, create it. Then create job directories.
        '''
        cfg, job_name = self.cfg, self.job_name
        out_top_dir = os.path.join(cfg.OUT_BASE_DIR, job_name)
        # Make sure the out directory exists etc.
        msg = f"{cfg.OUT_BASE_DIR} is not empty."
        assert os.path.exists(cfg.OUT_BASE_DIR), msg
        msg = f"{out_top_dir} is not empty."
        if os.path.exists(out_top_dir):
            assert os.path.isempty(out_top_dir), msg
        else:
            lg.info("Creating: ", out_top_dir)
            try:
                os.mkdir(out_top_dir)
            except Exception as e:
                lg.fail(e)
                exit(1)
        assert os.path.exists(out_top_dir), out_top_dir + " dne."
        return out_top_dir
    
    def create_grid_gpupeasy(self):
        cfg, job_name = self.cfg, self.job_name
        out_top_dir = self.__get_valid_outdir__()
        param_dict = cfg.get_paramdict()
        combs = [param_dict[keystr] for keystr in param_dict.keys()]
        # Get all possible point on the grid.
        combs = list(itertools.product(*combs))
        # We've lost our keystring information; restore it.
        combsdf = pd.DataFrame(combs)
        combsdf.columns = param_dict.keys()
        combsdf = cfg.reject_invalid(combsdf)
        assert len(combsdf) > 0, "No valid configurations found!"
        lg.info("Valid grid-points found:")
        lg.info('\n', combsdf)
        fname = job_name + '.esy'
        f = open(fname, 'w+')
        combs = combsdf.to_dict('records')
        for j, params in enumerate(combs):
            outdir = os.path.join(out_top_dir, 'job_%s' % j)
            lg.info("Creating:", outdir)
            os.mkdir(outdir)
            arg_str = ''
            for key in params.keys():
                arg_str += ' ' + key + ' ' + str(params[key])
            name = '%s_job_%s' % (job_name, j)
            outdir = os.path.join(out_top_dir, name)
            lg.info("Creating:", outdir)
            os.mkdir(outdir)
            cmd = f'python -u {cfg.SCRIPT} --out-folder {outdir} {arg_str}'
            outputfile = os.path.join(outdir, 'gpupeasy_logs.out')
            # Use print to write to file
            print(name, file=f, end=';;\n')
            print(outputfile, file=f, end=';;\n')
            print(cmd, file=f, end=';;;\n\n')
        lg.info("Copying grid to top directory:", out_top_dir)
        shutil.copy('./' + fname, out_top_dir)
        f.close()
        lg.info("Schedule: ")
        lg.info("DONE")

    def clean(self):
        cfg, job_name = self.cfg, self.job_name
        lg.info("Performing clean up")
        out_top_dir = os.path.join(cfg.OUT_BASE_DIR, job_name)
        msg = "Not found: " + cfg.OUT_BASE_DIR
        assert os.path.exists(cfg.OUT_BASE_DIR), msg
        assert os.path.isdir(cfg.OUT_BASE_DIR)
        out_top_dir_exists = False
        if os.path.exists(out_top_dir):
            out_top_dir_exists = True
            lg.warning("Top directory exists and will be removed: ",
                       out_top_dir)
        else:
            lg.info("Top directory not found: ", out_top_dir)
        # Check for .sh scripts or .esy
        files = os.listdir()
        scripts = [f for f in files if f.startswith(job_name)]
        if len(scripts) > 0:
            lg.warning("GPU scripts exists :", scripts)
            valid_f = [f'{job_name}.esy', f'{job_name}.sh']
            scripts = [f for f in files if f in valid_f]
            lg.warning("These will be removed: ", scripts)
        else:
            lg.info("No scripts found.")
        lg.info("Press any key to continue ...", end='')
        input()
        if out_top_dir_exists:
            try:
                lg.info("Removing: ", out_top_dir)
                shutil.rmtree(out_top_dir)
            except Exception as e:
                lg.fail("FAIL: Could not remove top directory", e)
                exit(1)
        for f in scripts:
            try:
                lg.info("Removing: ", f)
                os.remove('./' + f)
            except Exception as e:
                lg.fail("FAIL: Could not remove top script: ", f, e)
                exit(1)
        lg.info("Done.")


def CLIArgs():
    hstr = """A simple program to generate valid configurations supported by
    GPUPease for grid-searches. The exact grid is configured through the use of
    a gridconfig class (see example). This program produces a `.peasy` file for
    GPU-peasy. """
    parser = argparse.ArgumentParser(description=hstr)
    parser.add_argument("-g", "--grid-config", help="Python script with" +
                        "grid-config information.", required=True)
    parser.add_argument("-p", "--proj-name", help="Project name to use",
                        required=True)
    parser.add_argument("--clean", help="Clean the project directory.",
                        action='store_true', default=False)
    parser.add_argument("--build", help="Write grid configuration to .peasy" +
                        "file.", action="store_true", default=False)
    parser.add_argument("--cbuild", help="Equivalent to clean + build.",
                        default=False, action="store_true")
    args = parser.parse_args()
    action = None
    if args.clean:
        action = 'clean'
    elif args.build:
        action = 'build'
    elif args.cbuild:
        action = 'cbuild'
    args.action = action
    return args


def main():
    args = CLIArgs()
    cfg_file = args.grid_config
    proj_name = args.proj_name
    action = args.action
    ALL_ACTIONS = ['build', 'clean', 'cbuild']
    assert os.path.exists(cfg_file), f"File does not exist: {cfg_file}"
    cfg = __import__(cfg_file)
    grid = cfg.GRID_DICT[proj_name]
    gridgen = ValidGridGenerator(proj_name, grid)
    assert action in ALL_ACTIONS
    if action == 'clean':
        gridgen.clean()
    elif action == 'build':
        gridgen.create_grid_gpupeasy()
    elif action == 'cbuild':
        gridgen.clean()
        gridgen.create_grid_gpupeasy()
