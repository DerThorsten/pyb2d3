from ._pyb2d_samples import * # import all

from pathlib import Path
import os

data_dir = Path(os.path.join(os.path.dirname(__file__), 'data'))



def run_sample(cls):
    cls_name = str(cls.__name__)
    register_sample( cls, cls_name, cls_name)
    print("data_dir", data_dir)
    start_everything(str(data_dir), cls_name)
