import dataclasses
from typing import List, Union


@dataclasses.dataclass
class UAModelBase:
    model_uri: str
    publication_date: Union[str, None]
    version: Union[str, None]


@dataclasses.dataclass
class UARequiredModel(UAModelBase):
    def __hash__(self):
        key_to_hash = "{}_{}_{}".format(
            self.model_uri, self.publication_date, self.version
        )
        return hash(key_to_hash)


@dataclasses.dataclass
class UAModel(UAModelBase):
    required_models: List[UARequiredModel] = dataclasses.field(default_factory=list)
