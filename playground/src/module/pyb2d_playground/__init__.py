from ._pyb2d_playground import *  # import all

from pathlib import Path
import os

data_dir = Path(os.path.join(os.path.dirname(__file__), "data"))


# def run_sample(cls):
#     print("data_dir", data_dir)
#     start_everything(str(data_dir), cls)


def start_testbed(examples, starting_index=0):
    assert len(examples) > 0
    assert starting_index < len(examples)

    starting_example = tuple(examples[starting_index][1:])

    # check for duplicates
    conated_names = set(
        [f"{group_name}_{example_name}" for _, group_name, example_name in examples]
    )
    if len(conated_names) != len(examples):
        raise ValueError("Duplicate example names")

    # sort the examples by group name
    examples = sorted(examples, key=lambda x: x[1])

    # find the starting index
    starting_index = None
    for i, (cls, group_name, example_name) in enumerate(examples):
        if (group_name, example_name) == starting_example:
            starting_index = i
            break

    start_everything(str(data_dir), examples, starting_index)
