import typing

if typing.TYPE_CHECKING:
    from .database import BaseDatabase


class RegisterDatabaseLink:
    """This class tells register decorator to set _database link."""

    # Database link populated by register decorator
    _database: typing.Optional[typing.Type["BaseDatabase"]] = None

    pass
