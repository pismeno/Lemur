from pathlib import Path
import lemur
import lemur.utils.assets as lemur_assets

PROJECT_ROOT_PATH = Path(__file__).resolve().parent
PRIVATE_PATH = PROJECT_ROOT_PATH / "private"
PUBLIC_PATH = PROJECT_ROOT_PATH / "public"

LEMUR_ROOT = Path(lemur.__file__).resolve().parent
LEMUR_PRIVATE_PATH = LEMUR_ROOT / "private"
LEMUR_PUBLIC_PATH = LEMUR_ROOT / "public"

lemur_assets.PROJECT_ROOT_PATH = PROJECT_ROOT_PATH
lemur_assets.PRIVATE_PATH = PRIVATE_PATH
lemur_assets.PUBLIC_PATH = PUBLIC_PATH

lemur_assets.LEMUR_ROOT = LEMUR_ROOT
lemur_assets.LEMUR_PRIVATE_PATH = LEMUR_PRIVATE_PATH
lemur_assets.LEMUR_PUBLIC_PATH = LEMUR_PUBLIC_PATH

from lemur.kernel import application