from pkg_resources import resource_filename
import os

logging_path = resource_filename("protopipe_grid_interface", "logging.yaml")
print(logging_path)
package_dir = os.listdir(os.path.dirname(logging_path))
print(package_dir)
