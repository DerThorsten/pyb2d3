from ._pyb2d_samples import *  # import all

from pathlib import Path
import os

data_dir = Path(os.path.join(os.path.dirname(__file__), "data"))


def run_sample(cls):
    print("data_dir", data_dir)
    start_everything(str(data_dir), cls)
