#  Copyright 2021 Rikai Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import Iterator

import numpy as np
import pandas as pd
from pyspark.serializers import CloudPickleSerializer
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import BinaryType

from rikai.spark.sql.codegen.base import ModelSpec

__all__ = ["generate_udf"]

_pickler = CloudPickleSerializer()


def generate_udf(spec: ModelSpec):
    """Construct a UDF to run sklearn model.

    Parameters
    ----------
    spec : ModelSpec
        the model specifications object

    Returns
    -------
    A Spark Pandas UDF.
    """

    def sklearn_inference_udf(
        iter: Iterator[pd.Series],
    ) -> Iterator[pd.Series]:
        model = spec.model_type
        model.load_model(spec)
        for series in iter:
            X = np.vstack(series.apply(_pickler.loads).to_numpy())
            y = [_pickler.dumps(pred) for pred in model.predict(X)]
            yield pd.Series(y)

    return pandas_udf(sklearn_inference_udf, returnType=BinaryType())
