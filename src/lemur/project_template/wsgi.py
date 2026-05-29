from pathlib import Path
from lemur.utils.assets import set_project_root 

BASE_DIR = Path(__file__).resolve().parent

set_project_root(BASE_DIR)

from lemur.kernel import application