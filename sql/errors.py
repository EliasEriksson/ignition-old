class IgnitionException(Exception):
    details: dict

    def __init__(self, code: int) -> None:
        self.details = {"code": code}


class DuplicateEmail(IgnitionException):
    def __init__(self, email) -> None:
        super().__init__(1)
        self.details = self.details | {
            "email": email, "message": f"{email} is already in use."
        }

