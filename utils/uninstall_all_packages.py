import subprocess
import sys


def get_installed_packages():
    """Get a list of all installed packages using pip."""
    result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], stdout=subprocess.PIPE)
    packages = result.stdout.decode('utf-8').split('\n')
    return [pkg.split('==')[0] for pkg in packages if pkg]


def uninstall_package(package):
    """Uninstall a given package using pip."""
    subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', package])


def main():
    packages = get_installed_packages()
    for package in packages:
        uninstall_package(package)
    print("All pip-installed packages have been uninstalled.")


if __name__ == "__main__":
    main()
