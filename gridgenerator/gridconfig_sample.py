import numpy as np
import os
from gridgenerator.generator import driver, GridConfigBase


class GridConfigSample(GridConfigBase):
    OUT_BASE_DIR = os.environ['RDX_EXPS_DIR']
    SCRIPT = '/home/dondennis/Work/tensorrdx/rdx_exps/resnet_cifar/trainer.py'

    def __init__(self):
        """
        A sample grid configuration. To generate a custom grid configuration
        for your project;
            1. Extend the GridConfigBase class. The base class needs to be
            configured with a BASE_DIR and the script directory.
            BASE_DIR: The directory containing all project specific
            directories. Project directories will be created as
            sub-directories.
            2. Use `add_param` to add parameters to the grid.
            3. Use `__call__` to generate the final method.
        """ 
        super().__init__(GridConfigSample.OUT_BASE_DIR, GridConfigSample.SCRIPT)
        DATASET = ['CIFAR10']
        MODEL_VARIANT = ['ResNet20']
        BATCH_SIZE = [256]
        NUM_EPOCHS = [500]
        # POOL_DIM_1 will be made equal to Pool dim0
        POOL_DIM0 = [32, 128]
        FC_DIM0 = [8, 32, 256]
        SHORTC_IN = ['out0', 'out_l1', 'out_l2']
        SHORTC_OUT = ['out_l1', 'out_l2', 'out_l3']
        LOSS_LAMBDA = [10.0]
        SIGMA_BASE = [0.95]
        LEARNING_RATE = [0.1]
        RDX_ONLY = ['--rdx-only-training']

        self.add_param('--data-set', DATASET, str)
        self.add_param('--model-variant', MODEL_VARIANT, str)
        self.add_param('--batch-size', BATCH_SIZE, int)
        self.add_param('--num-epochs', NUM_EPOCHS, int)
        self.add_param('--pool-dim0', POOL_DIM0, int)
        self.add_param('--pool-dim1', POOL_DIM0, int)
        self.add_param('--fc-dim0', FC_DIM0, int)
        self.add_param('--fc-dim1', FC_DIM0, int)
        self.add_param('--shortc-in', SHORTC_IN, str)
        self.add_param('--shortc-out', (SHORTC_OUT), str)
        self.add_param('--loss-lambda', LOSS_LAMBDA, float)
        self.add_param('--sigma-base', SIGMA_BASE, float)
        self.add_param('--learning-rate', LEARNING_RATE, float)
        self.add_param('--rdx-only-training', RDX_ONLY, str)
        self.reject_invalid = self.rej_invalid1

    def __repr__(self):
        return "ExA1: Basic grid search. Fc_dim0 = fc_dim1, same for rnn."

    def __str__(self):
        return self.__repr__()

    def rej_invalid1(self, cordsdf):
        '''
        cords: A list of dicts. Each dict contains a keystring -> value pair.

        1. reject all jobs where shortc_in >= shortc_out
        2. reject all jobs where fc_hid0 != fc_hid1
        3. reject all jobs where pool_hid0 != pool_hid1
        '''
        # Remove all where hid dimensions differ
        df = cordsdf
        df = df[df['--fc-dim0'] == df['--fc-dim1']]
        df = df[df['--pool-dim0'] == df['--pool-dim1']]
        # Remove all where in >= out
        in_, out_ = df['--shortc-in'].values, df['--shortc-out'].values
        in_int = [int(x_[-1]) for x_ in in_]
        out_int = [int(x_[-1]) for x_ in out_]
        indices = np.array(in_int) < np.array(out_int)
        df = df[indices]
        return df


if __name__ == '__main__':
    grid_dict = {
        'ExA1': GridConfigExA1
    }
    driver(grid_dict)


