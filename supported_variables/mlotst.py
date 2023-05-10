if __name__ == "__main__":
    from supported_variables.utils.supported_variable import (
        supported_variable,
        preprocessing,
    )
    import utils.utils as utils
else:
    from supported_variables.utils.supported_variable import (
        supported_variable,
        preprocessing,
    )
    import supported_variables.utils.utils as utils
from cdo import Cdo
from typing import List, Tuple, Union
import os.path as path


@supported_variable
class Mlotst:
    realm = "o"


# Mixed layer data is not saved in annual mean data,
# so we need to calculate the annual mean from monthly data
@preprocessing(Mlotst, "BRIDGE-monthly-to-annual")
def preprocessing_1(
    inputs: List[Tuple[str, str]], output_directory: str
) -> List[Tuple[str, str]]:
    cdo = Cdo()

    file, var = inputs[0]

    name = path.basename(file).replace(".nc", ".out.nc")
    output = path.join(output_directory, name)

    output = cdo.sellonlatbox(
        "-180,180,90,-90", input=f" -yearmean {file}", options="-r -f nc"
    )

    return [(output, var)]
