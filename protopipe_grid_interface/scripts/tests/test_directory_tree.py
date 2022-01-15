from pathlib import Path
import subprocess
from pkg_resources import resource_filename
import pytest
import yaml

from protopipe_grid_interface.utils import load_config


def test_directory_tree(tmpdir):

    pytest.importorskip("protopipe", minversion="0.5.0")

    test_analysis_workflow = tmpdir.join("test_analysis_workflow.yaml")

    tree = {
        "configs": [],
        "data": {
            "simtel": [],
            "TRAINING": {
                "for_energy_estimation": ["gamma"],
                "for_particle_classification": ["gamma", "proton"],
            },
            "DL2": ["gamma", "proton", "electron"],
            "DL3": [],
        },
        "estimators": ["energy_regressor", "gamma_hadron_classifier"],
    }

    with open(str(test_analysis_workflow), "w") as file:
        yaml.dump(tree, file)

    subprocess.run(
        [
            "python",
            resource_filename(
                "protopipe_grid_interface", "scripts/create_analysis_tree.py"
            ),
            "--analysis_name",
            "test_analysis",
            "--analysis_directory_tree",
            test_analysis_workflow,
            "--GRID-is-DIRAC",
            "--GRID-home",
            "home_test",
            "--output_path",
            tmpdir,
        ],
        check=True,
    )

    analysis_path = tmpdir / "shared_folder/analyses/test_analysis"

    metadata_file_path = analysis_path / "analysis_metadata.yaml"
    assert metadata_file_path.exists()

    # load metadata and check that we get back what we built
    with open(metadata_file_path, "r") as f:
        metadata = yaml.load(f, Loader=yaml.CLoader)
        assert metadata["analysis_name"] == "test_analysis"
        assert metadata["analyses_directory"] == str(tmpdir / "shared_folder/analyses")
        assert metadata["GRID is DIRAC"] == True
        assert metadata["Home directory on the GRID"] == "home_test"
        assert metadata["analysis directory on the GRID from home"] == ""

    # Check that the created directory tree is the expected one
    assert analysis_path.exists()
    assert (analysis_path / "configs").exists()
    assert (analysis_path / "data/simtel").exists()
    assert (analysis_path / "data/TRAINING/for_energy_estimation/gamma").exists()
    assert (analysis_path / "data/TRAINING/for_particle_classification/gamma").exists()
    assert (analysis_path / "data/TRAINING/for_particle_classification/proton").exists()
    assert (analysis_path / "data/DL2/gamma").exists()
    assert (analysis_path / "data/DL2/proton").exists()
    assert (analysis_path / "data/DL2/electron").exists()
    assert (analysis_path / "data/DL3").exists()
    assert (analysis_path / "estimators/energy_regressor").exists()
    assert (analysis_path / "estimators/gamma_hadron_classifier").exists()
