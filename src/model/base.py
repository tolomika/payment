import re

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    id: Any
    __abstract__ = True
    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(cls):
        """
        Converts CamelCase to snake_case for table names.

        >>> camel_case_to_snake_case("SomeSDK")
        'some_sdk'
        """
        name = cls.__name__
        snake_case_name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return snake_case_name

    @property
    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
