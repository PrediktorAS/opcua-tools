import dataclasses
from typing import List, Union


@dataclasses.dataclass
class UAModelBase:
    model_uri: str
    publication_date: Union[str, None]
    version: str


@dataclasses.dataclass
class UARequiredModel(UAModelBase):
    pass


@dataclasses.dataclass
class UAModel(UAModelBase):
    required_models: List[UARequiredModel] = dataclasses.field(default_factory=list)
