import os
import subprocess
import re
from tomlkit import parse, dumps

# 1. Path to your project and files
project_path = os.getcwd()  # Get the directory from which the script is called
# project_path = os.path.abspath(
#     os.path.dirname(__file__))  # Automatically gets current script path
pyproject_file = os.path.join(project_path, "pyproject.toml")
setup_file = os.path.join(project_path, "setup.py")
requirements_temp = os.path.join(project_path, "temp_requirements.txt")


# 2. Function to run pipreqs and generate the minimal requirements list
def run_pipreqs():
    subprocess.run(["pipreqs", project_path, "--savepath", requirements_temp],
                   check=True)


# 3. Parse the output of pipreqs (from temp_requirements.txt)
def parse_requirements(file):
    with open(file, "r") as f:
        lines = f.readlines()
    requirements = {}
    for line in lines:
        if "==" in line:
            package, version = line.strip().split("==")
            requirements[package] = version
    return requirements


# 4. Function to update pyproject.toml
def update_pyproject(pyproject_file, requirements):
    with open(pyproject_file, "r") as f:
        content = f.read()

    pyproject = parse(content)

    # Check if 'dependencies' exists under 'project', if not, create it
    if "project" not in pyproject:
        pyproject["project"] = {}

    if "dependencies" not in pyproject["project"]:
        pyproject["project"]["dependencies"] = []

    dependencies = pyproject["project"]["dependencies"]

    # Clear existing dependencies and add new ones as a list (array)
    dependencies.clear()

    # tomlkit handles adding dependencies line-by-line automatically
    for package, version in requirements.items():
        dependencies.append(f"{package}=={version}")

    # Mark the array as multiline to force new lines in the output
    dependencies.multiline(True)

    # Save the updated pyproject.toml with proper formatting
    with open(pyproject_file, "w") as f:
        f.write(dumps(pyproject))
    print(f"Updated {pyproject_file} with new dependencies.")


# 5. Function to update setup.py
def update_setup_py(setup_file, requirements):
    with open(setup_file, "r") as f:
        content = f.read()

    # Regular expression to find the existing install_requires block
    install_requires_pattern = re.compile(r"install_requires=\[(.*?)\]", re.DOTALL)

    # Replace the old install_requires content with the new one
    install_requires_block = ",\n        ".join(
        [f'"{pkg}=={ver}"' for pkg, ver in requirements.items()])
    new_content = install_requires_pattern.sub(
        f"install_requires=[{install_requires_block}]", content)

    # Save the updated setup.py
    with open(setup_file, "w") as f:
        f.write(new_content)
    print(f"Updated {setup_file} with new dependencies.")


# 6. Prompt the user for confirmation before updating
def prompt_user_confirmation(file_type):
    response = input(f"Do you want to update {file_type}? [Y/n]: ").lower().strip()
    return response in ("y", "yes", "")


# 7. Main function to handle updates for both pyproject.toml and setup.py
def update_dependencies():
    files_found = False

    # Step 1: Run pipreqs
    run_pipreqs()

    # Step 2: Parse requirements from pipreqs output
    requirements = parse_requirements(requirements_temp)

    # Step 3: Check for pyproject.toml and setup.py, prompt user for confirmation
    if os.path.exists(pyproject_file):
        files_found = True
        if prompt_user_confirmation("../pyproject.toml"):
            update_pyproject(pyproject_file, requirements)
        else:
            print("pyproject.toml update skipped.")

    if os.path.exists(setup_file):
        files_found = True
        if prompt_user_confirmation("setup.py"):
            update_setup_py(setup_file, requirements)
        else:
            print("setup.py update skipped.")

    # Step 4: Clean up the temporary requirements file
    if os.path.exists(requirements_temp):
        os.remove(requirements_temp)
        print(f"Deleted temporary file: {requirements_temp}")

    # Step 5: Handle case where neither file exists
    if not files_found:
        print("No pyproject.toml or setup.py file was found in the current directory.")


if __name__ == "__main__":
    update_dependencies()
