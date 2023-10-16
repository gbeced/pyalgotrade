import os



def getRootDirectory():
    # Specify the name of the known file at the root
    root_marker = "setup.py"
    # Get the script's directory
    script_directory = os.path.dirname(__file__)
    # Traverse up the directory tree to find the root directory
    root_directory = script_directory
    while root_directory != '/' and root_marker not in os.listdir(root_directory):
        root_directory = os.path.dirname(root_directory)
    print("Project Root Directory:", root_directory)
    return root_directory


def get_data_file_path(fileName):
    return os.path.join(get_dump_folder(), fileName)

def get_dump_folder():
    return os.path.join(getRootDirectory(), "Dump")


def getNSEFileName(symbol, startdate, enddate):
    return symbol + '-' + startdate.year.__str__() + '-' + enddate.year.__str__() + "-" + "nsedt"
