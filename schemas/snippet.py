import uuid
from pydantic import BaseModel, constr
from pydantic.typing import Literal as Enum
from ignition.common.languages import Languages
from sql import models
supported_languages = Enum[tuple(Languages.languages)]


class SnippetBase(BaseModel):
    language: Enum[supported_languages]
    # property not detected by pycharm inspection
    # noinspection PyUnresolvedReferences
    code: constr(max_length=models.Snippet.code.property.columns[0].type.length)
    # property no detected by pycharm inspection
    # noinspection PyUnresolvedReferences
    args: constr(max_length=models.Snippet.args.property.columns[0].type.length)


class SnippetData(SnippetBase):
    pass


class Snippet(SnippetBase):
    id: uuid.UUID

    class Config:
        orm_mode = True


class SnippetResponse(SnippetBase):
    id: uuid.UUID

    class Config:
        orm_mode = True
