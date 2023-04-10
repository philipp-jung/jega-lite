import math
from enum import Enum
from typing import Any

import pandas as pd
from basis import (
    BinaryClassificationTask,
    MultiClassClassificationTask,
    RegressionTask,
    Task,
)
from data import read_dataset
from pandas.api.types import is_numeric_dtype
from sklearn.metrics import f1_score, mean_absolute_error, mean_squared_error
from utils import is_categorical


class TaskType(str, Enum):
    BINARY = "binary"
    MULTI_CLASS = "multi_class"
    REGRESSION = "regression"

class OpenMLTask(Task):
    def __init__(
        self,
        openml_id: int,
        corruption: str | None = None,
        fraction: float | None = None,
        seed: int | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Minor changes of https://github.com/schelterlabs/jenga/blob/c219c645c664d2e81b7dfab2c51262e64e20f4ab/src/jenga/tasks/openml.py#L15  # noqa: E501."""
        if (corruption is not None and fraction is None) or (corruption is None and fraction is not None):
            raise Exception("Either set 'corruption' and 'fraction' or none of them!")

        train_data, train_labels = read_dataset(task_id=openml_id, training=True)
        test_data, test_labels = read_dataset(
            task_id=openml_id, training=False, corruption=corruption, fraction=fraction,
        )

        categorical_columns = [column for column in train_data.columns if is_categorical(train_data[column])]
        numerical_columns = [
            column
            for column in train_data.columns
            if is_numeric_dtype(train_data[column]) and column not in categorical_columns
        ]

        super().__init__(
            train_data=train_data,
            train_labels=train_labels,
            test_data=test_data,
            test_labels=test_labels,
            categorical_columns=categorical_columns,
            numerical_columns=numerical_columns,
            is_image_data=False,
            seed=seed,
        )

    def calculate_performance(self, data: pd.DataFrame) -> tuple[float, float, float]:
        # jenga does this, so we need to do this here as well to avoid downstream errors
        data = data.copy()
        for col in self.categorical_columns:
            data[col] = data[col].astype(str)
        predictions = self._baseline_model.predict(data)
        return self.score_on_test_data(predictions)


class OpenMLRegressionTask(OpenMLTask, RegressionTask):
    """Class that represents a regression task and
    gets data from [OpenML](https://www.openml.org).
    """

    def score_on_test_data(self, predictions: pd.DataFrame) -> tuple[float, float, float]:
        return (
            mean_absolute_error(self.test_labels, predictions),
            mean_squared_error(self.test_labels, predictions),
            math.sqrt(mean_squared_error(self.test_labels, predictions)),
        )


class OpenMLMultiClassClassificationTask(OpenMLTask, MultiClassClassificationTask):
    """Class that represents a multi-class classification task and
    gets data from [OpenML](https://www.openml.org).
    """

    def score_on_test_data(self, predictions: pd.DataFrame) -> tuple[float, float, float]:
        return (
            f1_score(self.test_labels, predictions, average="micro"),
            f1_score(self.test_labels, predictions, average="macro"),
            f1_score(self.test_labels, predictions, average="weighted"),
        )


class OpenMLBinaryClassificationTask(OpenMLTask, BinaryClassificationTask):
    """Class that represents a binary classification task and
    gets data from [OpenML](https://www.openml.org).
    """

    def score_on_test_data(self, predictions: pd.DataFrame) -> tuple[float, float, float]:
        return (
            f1_score(self.test_labels, predictions, average="micro"),
            f1_score(self.test_labels, predictions, average="macro"),
            f1_score(self.test_labels, predictions, average="weighted"),
        )


def get_OpenMLTask(
    task_id: int,
    task_type: TaskType,
    corruption: str | None = None,
    fraction: float | None = None,
    **kwargs: dict[str, Any],
) -> OpenMLTask:

    if (corruption is not None and fraction is None) or (corruption is None and fraction is not None):
        raise Exception("Either set 'corruption' and 'fraction' or none of them!")

    if task_type == TaskType.BINARY:
        return OpenMLBinaryClassificationTask(
            openml_id=task_id, corruption=corruption, fraction=fraction, kwargs=kwargs,
        )

    elif task_type == TaskType.MULTI_CLASS:
        return OpenMLMultiClassClassificationTask(
            openml_id=task_id, corruption=corruption, fraction=fraction, kwargs=kwargs,
        )

    elif task_type == TaskType.REGRESSION:
        return OpenMLRegressionTask(openml_id=task_id, corruption=corruption, fraction=fraction, kwargs=kwargs)
