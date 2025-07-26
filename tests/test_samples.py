import pytest
import sys
from pathlib import Path
from pyb2d3.samples import SampleBase
from .headless_test_frontend import run_in_headless_test_frontend


this_dir = Path(__file__).parent
pyb2d_dir = this_dir.parent
examples_dir = pyb2d_dir / "examples"

# add examples directory to the path
sys.path.append(str(examples_dir))
import pyb2d3_samples  # noqa: E402


def test_import_samples():
    assert pyb2d3_samples is not None, "Failed to import pyb2d3_samples"


print(f"SampleBase subclasses: {SampleBase.subclasses}")


def test_subclass_exists():
    assert SampleBase.subclasses is not None
    assert len(SampleBase.subclasses) > 0, "No subclasses of SampleBase found"


# parametrize the test with all subclasses of SampleBase
@pytest.mark.parametrize("sample_class", SampleBase.subclasses)
def test_sample_class(sample_class):
    run_in_headless_test_frontend(
        sample_class=sample_class, sample_settings=sample_class.Settings()
    )
