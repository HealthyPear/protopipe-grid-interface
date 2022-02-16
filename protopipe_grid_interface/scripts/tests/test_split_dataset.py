import subprocess
from pkg_resources import resource_filename


def test_simple_split(tmpdir):

    original_list = tmpdir.join("original_list.list")

    with open(str(original_list), mode="w", encoding="utf8") as file:
        for i in range(10):
            file.write(f"{i}\n")

    subprocess.run(
        [
            "python",
            resource_filename("protopipe_grid_interface", "scripts/split_dataset.py"),
            "--input_gammas",
            original_list.strpath,
            "--split_gammas",
            "10",
            "10",
            "80",
            "--output_path",
            tmpdir.strpath,
        ],
        check=True,
    )

    list1 = tmpdir.join("original_list_TRAINING_ENERGY.list")
    list2 = tmpdir.join("original_list_TRAINING_CLASSIFICATION.list")
    list3 = tmpdir.join("original_list_PERFORMANCE.list")

    with open(str(list1), mode="r", encoding="utf8") as file:
        lines_list1 = len(file.readlines())
    with open(str(list2), mode="r", encoding="utf8") as file:
        lines_list2 = len(file.readlines())
    with open(str(list3), mode="r", encoding="utf8") as file:
        lines_list3 = len(file.readlines())

    assert lines_list1 == 1
    assert lines_list2 == 1
    assert lines_list3 == 8
