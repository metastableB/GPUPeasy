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
from tqdm import trange
from gridgenerator.utils import CLog as lg


class GridConfigBase:

    def __init__(self, OUT_BASE_DIR, SCRIPT, SUMMARY_KEYS=None):
        self.__call_called = False
        self.__grid_dict = {}
        self.__grid_str_func = {}
        self.OUT_BASE_DIR = OUT_BASE_DIR
        self.SCRIPT = SCRIPT
        self.SUMMARY_KEYS = SUMMARY_KEYS

    def add_param(self, keystring, val):
        self.__grid_dict[keystring] = val

    def var_to_key(self, var):
        #ARG_A_B_C
        var = '--' + '-'.join(var[4:].split('_'))
        return var

    def __call__(self):
        args = self.__dict__
        vargs = [k for k in args.keys() if k.startswith('ARG')]
        for var in vargs:
            k = self.var_to_key(var)
            self.add_param(k, args[var])
        self.__call_called = True

    def get_param(self, keystring):
        if not self.__call_called:
            lg.fail("__call__ not invoked")
            exit()
        self.__grid_dict[keystring]

    def get_paramdict(self):
        if not self.__call_called:
            lg.fail("__call__ not invoked")
            exit()
        return self.__grid_dict

    def reject_invalid(self):
        raise NotImplementedError

    def extractor(self, keys, alldata):
        """
        Return a dict of value, for each element in keys. This will be used to
        summarize experiments.
        """
        raise NotImplementedError

    def show(self, dfsumm):
        """
        override to display summary dataframe
        """
        raise NotImplementedError

    def __repr__(self):
        if self.__doc__:
            return self.__doc__
        return "No docstring provided"

    def __str__(self):
        return self.__repr__()


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
            assert len(os.listdir(out_top_dir)) == 0, msg
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
        lg.info("Project:\n\n", self.cfg, "\n")
        combsdf, job_list = self.__create_grid()
        fname = job_name + '.esy'
        f = open(fname, 'w+')
        for job in job_list:
            name, outf = job['name'], job['out_file']
            cmd = job['cmd']
            print(name, file=f, end=';;\n')
            print(outf, file=f, end=';;\n')
            print(cmd, file=f, end=';;;\n\n')
        csv_name = job_name + '.csv'
        combsdf.to_csv(csv_name, index=False)
        lg.info("\n", combsdf)
        lg.info("Copying grid to top directory:", out_top_dir)
        shutil.copy('./' + fname, out_top_dir)
        shutil.copy('./' + csv_name, out_top_dir)
        f.close()
        lg.info("Schedule: ")
        lg.info("DONE")

    def get_grid(self):
        job_names, job_logs, job_cmds = [], [], []
        cfg, job_name = self.cfg, self.job_name
        out_top_dir = self.__get_valid_outdir__()
        combsdf, job_list = self.__create_grid()
        for job in job_list:
            name, outf = job['name'], job['out_file']
            cmd = job['cmd']
            job_names.append(name)
            job_logs.append(outf)
            job_cmds.append(cmd)
        df = pd.DataFrame({
            'Job-name':job_names,
            'Output-file': job_logs,
            'Job-command': job_cmds}
        )
        return df, combsdf
    
    def __create_grid(self, ordering=None):
        cfg, job_name = self.cfg, self.job_name
        out_top_dir = self.__get_valid_outdir__()
        param_dict = cfg.get_paramdict()
        combs = [param_dict[keystr] for keystr in param_dict.keys()]
        # Get all possible point on the grid.
        combs = list(itertools.product(*combs))
        # We've lost our keystring information; restore it.
        combsdf = pd.DataFrame(combs)
        combsdf.columns = param_dict.keys()
        combsdf = cfg.reject_invalid(combsdf).reset_index(drop=True)
        assert len(combsdf) > 0, "No valid configurations found!"
        combs = combsdf.to_dict('records')
        out_dir_list = []
        job_list = []
        for j, params in enumerate(combs):
            arg_str = ''
            if ordering is None:
                keyordering = params.keys()
            for key in keyordering:
                if pd.notnull(params[key]):
                    arg_str += ' ' + key + ' ' + str(params[key])
            name = '%s_job_%s' % (job_name, j)
            outdir = os.path.join(out_top_dir, name)
            out_dir_list.append(outdir)
            os.mkdir(outdir)
            cmd = f'python -u {cfg.SCRIPT} --out-dir {outdir} {arg_str}'
            outputfile = os.path.join(outdir, 'gpupeasy_logs.out')
            # Use print to write to file
            job_list.append({'name': name, 'out_file': outputfile,
                             'cmd': cmd})

        combsdf['JOB_DIR'] = out_dir_list
        return combsdf, job_list

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
            valid_f = [f'{job_name}.esy', f'{job_name}.csv']
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


def summarizer(projname, gridconfig):
        """
        A quick way to provide and extract summaries. Needs the `extractor()`
        function and `SUMMARY_KEYS` to be defined.
        """
        extractor = gridconfig.extractor
        keys = gridconfig.SUMMARY_KEYS
        assert keys is not None, "No keys provided to summarize"
        exp_path = gridconfig.OUT_BASE_DIR
        exp_path = os.path.join(exp_path, projname)
        assert os.path.exists(exp_path), f"Not found: {exp_path}"
        # If found, load the dataframe containing the parameters
        dfpath = os.path.join(exp_path, projname + '.csv')
        paramdf = pd.read_csv(dfpath)
        file_list = paramdf['JOB_DIR'].values
        valdict = {k: [] for k in keys}
        with trange(len(file_list)) as t:
            for i in t:
                f = os.path.join(file_list[i], 'gpupeasy_logs.out')
                if not os.path.exists(f):
                    f = os.path.join(file_list[i], 'slurm.log')
                if os.path.exists(f):
                    t.set_description(f'Processing: {f}')
                    with open(f, 'r') as fp:
                        data = fp.read()
                        ret = extractor(keys, data)
                else:
                    lg.warning("Log file not found: ", file_list[i])
                    ret = extractor(keys, '')
                # Description will be displayed on the left
                for key in keys:
                    valdict[key].extend(ret[key])
        for key in keys:
            paramdf[key] = valdict[key]
        return paramdf


def CLIArgs():
    hstr = """v0.1\nA simple program to generate valid configurations supported
    by GPUPease for grid-searches. The exact grid is configured through the use
    of a gridconfig class (see example). This program produces a `.peasy` file
    for GPU-peasy. """
    parser = argparse.ArgumentParser(description=hstr)
    parser.add_argument("-p", "--proj-name", help="Project name to use",
                        required=True)
    parser.add_argument("action", help="Action to take in " +
                        "[summarize, build, clean, cbuild]")
    args = parser.parse_args()
    return args


def driver(grid_dict):
    """
    gird_dict: A dictionary mapping project names to corresponding grid-gen
        classes.
    """
    args = CLIArgs()
    proj_name = args.proj_name
    action = args.action
    ALL_ACTIONS = ['build', 'clean', 'cbuild', 'summarize']
    #__init__()__call__()
    grid = grid_dict[proj_name]()
    grid()
    gridgen = ValidGridGenerator(proj_name, grid)
    assert action in ALL_ACTIONS
    lg.info("Performing: ", action)
    if action == 'clean':
        gridgen.clean()
    elif action == 'build':
        gridgen.create_grid_gpupeasy()
    elif action == 'cbuild':
        gridgen.clean()
        gridgen.create_grid_gpupeasy()
    elif action == 'summarize':
        df = summarizer(proj_name, grid)
        grid.show(df)
