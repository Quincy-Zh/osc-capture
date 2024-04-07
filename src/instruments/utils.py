#
import os
from datetime import datetime


def get_filepath(dir_):
    n = datetime.now()
    filename = n.strftime('%Y%m%d_%H%M%S_%f.png')

    return os.path.join(dir_, filename)
