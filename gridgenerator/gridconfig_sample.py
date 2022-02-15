import numpy as np


class GridConfigBase:
    # The base directory to use. Logs for each job will be saved in
    # job-specific folder under
    #   base_dir/proj_name/job_id*
    #
    # Example: OUT_BASE_DIR = os.path.join(os.environ['MODEL_DUMP_NOISE'], 'rdx0')
    OUT_BASE_DIR = None
    # The script to run
    f = 'rdx/train_ccnn_rdx.py'
    SCRIPT = '/home/t-dondennis/noisesupp/scripts/' + f

    def __init__(self):
        self.__grid_dict = {}
        self.__grid_str_func = {}

    def add_param(self, keystring, val, strfunc):
        '''
        strfunc: The function to use to convert an individual value to string
        '''
        self.__grid_dict[keystring] = val
        self.__grid_str_func[keystring] = val

    def get_param(self, keystring):
        self.__grid_dict[keystring]

    def get_str_val(self, keystring, val):
        '''
        Converts value for key to string using provided conversion method
        '''
        return self.__grid_str_func[keystring](val)

    def get_paramdict(self):
        return self.__grid_dict

    def reject_invalid(self):
        raise NotImplementedError


class GridConfigExD1(GridConfigBase):
    def __init__(self):
        super().__init__()
        NUM_ITER = [600]
        NUM_EPOCH = [300]
        SHORTC_IN = ['enc03', 'enc05', 'enc06']
        SHORTC_OUT = ['enc07', 'enc08', 'enc10']
        HID_DIM0 = [256, 512]
        HID_DIM1 = [256, 512]
        RDX_NAME = ['rnnpool']
        CKPT_FILE = ['/data/t-dondennis/MODEL_DUMP_2/noisesupp/kaz_noise/'
                     + 'v141d00_model/out/model.ckpt-288']
        self.add_param('--num-itr', NUM_ITER, str)
        self.add_param('--epochs', NUM_EPOCH, str)
        self.add_param('--shortc-in', SHORTC_IN, str)
        self.add_param('--shortc-out', (SHORTC_OUT), str)
        self.add_param('--hid-dim0', (HID_DIM0), str)
        self.add_param('--hid-dim1', (HID_DIM1), str)
        self.add_param('--rdx-name', RDX_NAME, str)
        self.add_param('--model-file', CKPT_FILE, str)
        self.reject_invalid = self.rej_invalid1

    def __repr__(self):
        return "Test config"

    def __str__(self):
        return self.__repr__()

    def rej_invalid1(self, cordsdf):
        '''
        cords: A list of dicts. Each dict contains a keystring -> value pair.

        1. reject all jobs where shortc_in >= shortc_out
        2. reject all jobs where hid0 != hid1
        '''
        # Remove all where hid dimensions differ
        df = cordsdf
        df = df[df['--hid-dim0'] == df['--hid-dim1']]
        # Remove all where in >= out
        in_, out_ = df['--shortc-in'].values, df['--shortc-out'].values
        in_ = [int(x[3:]) for x in in_]
        out_ = [int(x[3:]) for x in out_]
        indices = np.array(in_) < np.array(out_)
        df = df[indices]
        return df


