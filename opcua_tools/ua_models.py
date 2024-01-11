import dataclasses


@dataclasses.dataclass
class UAModelBase:
    model_uri: str
    publication_date: str | None
    version: str


@dataclasses.dataclass
class UARequiredModel(UAModelBase):
    pass


@dataclasses.dataclass
class UAModel(UAModelBase):
    required_models: list[UARequiredModel] = dataclasses.field(default_factory=list)
