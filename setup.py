import os
from setuptools import setup, find_packages

extras_require = {
    "tests": [
        "pytest",
        "pytest-cov",
        "pytest-dependency",
        "codecov",
        "pyyaml",
        "tables",
    ],
}

extras_require["all"] = list(set(extras_require["tests"]))


setup(
    name="protopipe-grid-interface",
    description="Interface to the DIRAC grid for the prototype pipeline for the Cherenkov Telescope Array (CTA)",
    keywords="cta pipeline simulations grid",
    url="https://github.com/HealthyPear/protopipe-grid-interface",
    project_urls={  # same as protopipe
        "Documentation": "https://cta-observatory.github.io/protopipe/",
        "Source": "https://github.com/HealthyPear/protopipe-grid-interface",
        "Tracker": "https://github.com/cta-observatory/protopipe/issues",
        "Projects": "https://github.com/cta-observatory/protopipe/projects",
    },
    author="Michele Peresano",
    author_email="michele.peresano@cea.fr",
    license="CeCILL-B Free Software License Agreement",
    packages=find_packages(),
    package_data={
        "protopipe_grid_interface": ["aux/standard_analysis_workflow.yaml", "grid.yaml"]
    },
    install_requires=["DIRAC", "CTADIRAC", "pyyaml", "tables", "tqdm"],
    zip_safe=False,
    use_scm_version={
        "write_to": os.path.join("protopipe_grid_interface", "_version.py")
    },
    tests_require=extras_require["tests"],
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Physics",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.7",
    extras_require={
        "all": extras_require["tests"],
        "tests": extras_require["tests"],
    },
    entry_points={
        "console_scripts": [
            "protopipe-SPLIT_DATASET=protopipe_grid_interface.scripts.split_dataset:main",
            "protopipe-CREATE_ANALYSIS=protopipe_grid_interface.scripts.create_analysis_tree:main",
            "protopipe-SUBMIT_JOBS=protopipe_grid_interface.scripts.submit_jobs:main",
            "protopipe-DELETE_FILES=protopipe_grid_interface.scripts.delete_files:main",
            "protopipe-DOWNLOAD_FILES=protopipe_grid_interface.scripts.download_files:main",
            "protopipe-MERGE_FILES=protopipe_grid_interface.scripts.merge_tables:main",
            "protopipe-DOWNLOAD_AND_MERGE=protopipe_grid_interface.scripts.download_and_merge:main",
            "protopipe-UPLOAD_FILE=protopipe_grid_interface.scripts.upload_file:main",
            "protopipe-UPLOAD_MODELS=protopipe_grid_interface.scripts.upload_models:main",
            "protopipe-FORCE_JOB_TO_FAILED=protopipe_grid_interface.scripts.cta_wms_set_failed:main",
            # "protopipe-FILTER-REPLICAS=protopipe_grid_interface.scripts.filter_lfns_by_replicas:main",
        ],
    },
)
