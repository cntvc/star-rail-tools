import pydantic

__all__ = ["DBModel", "Field_Ex"]


class DBModel(pydantic.BaseModel):
    __sql_table__ = []
    """子类注册表"""

    @staticmethod
    def _register(subclass):
        DBModel.__sql_table__.append(subclass)

    def __init_subclass__(cls):
        cls._register(cls)


def Field_Ex(primary_key=False, **kwargs):
    d = {"primary_key": primary_key}
    return pydantic.Field(json_schema_extra=d, **kwargs)
