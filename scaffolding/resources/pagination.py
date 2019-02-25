from typing import Optional

from ..exc import Exceptions
from ..security import SimpleSymmetricEncryption


class Pagination:
    """Encrypts the last object's id for the next query to start from.

    Usage::

        key_material = load_from_db()
        pagination = Pagination.with_symmetric_key(key_material)

        def list_users(caller, previous_token):
            q = query(Users).limit(pagination.limit + 1)

            # validate that the token came from this account, then apply it to the query if it's provided
            previous_token = pagination.unpack(previous_token, account_id=caller)
            if previous_token:
                q = q.filter(Users.id > previous_token)

            results = q.all()
            # include the next token in the response
            next_token = pagination.pack(results[-1].id, account_id=caller)
            return {"users": page, pagination.parameter_name: token}

    """
    def __init__(
            self, *,
            limit: int = 100,
            parameter_name: str = "continuationToken",
            encryption: SimpleSymmetricEncryption = None) -> None:
        if encryption is None:
            encryption = SimpleSymmetricEncryption()
        # by default, uses "values[-1].id" to get the last id

        self.limit = limit
        self.parameter_name = parameter_name
        self.encryption = encryption

    def pack(self, next_token: Optional[str], account_id: str = None) -> str:
        if next_token is None:
            return ""
        return self.encryption.encrypt(next_token, account_id=account_id)

    def unpack(self, previous_token: Optional[str], account_id: str = None) -> Optional[str]:
        if not previous_token:
            return None
        token = self.encryption.decrypt(previous_token, account_id=account_id)
        if token is None:
            raise Exceptions.invalid_parameter(
                name=self.parameter_name,
                value=previous_token,
                constraint="be a valid continuation token for your account")
        return token

    @classmethod
    def with_symmetric_key(cls, key_material: bytes, encryption_cls=SimpleSymmetricEncryption) -> "Pagination":
        encryption = encryption_cls(key_material=key_material)
        return cls(encryption=encryption)
