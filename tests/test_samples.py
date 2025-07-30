import pytest
import sys
from pathlib import Path
from .headless_test_frontend import run_in_headless_test_frontend


this_dir = Path(__file__).parent
pyb2d_dir = this_dir.parent
examples_dir = pyb2d_dir / "examples"

# add examples directory to the path
sys.path.append(str(examples_dir))
import pyb2d3_samples  # noqa: E402


def test_import_samples():
    assert pyb2d3_samples.all_examples is not None

    for example in pyb2d3_samples.all_examples:
        assert example is not None


def test_subclass_exists():
    assert len(pyb2d3_samples.all_examples) > 0, "No examples found in pyb2d3_samples"


# parametrize the test with all subclasses of SampleBase
@pytest.mark.parametrize("sample_class", pyb2d3_samples.all_examples)
def test_sample_class(sample_class):
    # we want to print the name of the sample class being tested
    print(f"Testing sample class: {sample_class.__name__}")

    run_in_headless_test_frontend(
        sample_class=sample_class, sample_settings=sample_class.Settings()
    )
