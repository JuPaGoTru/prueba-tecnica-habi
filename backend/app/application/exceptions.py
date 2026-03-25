class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class NotFoundError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


class AlreadyMemberError(Exception):
    pass


class CannotModifyOwnerError(Exception):
    pass


class ConflictError(Exception):
    pass
