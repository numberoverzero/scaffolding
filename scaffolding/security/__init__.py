import logging
import secrets
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError
from cryptography.fernet import Fernet

from ..exc import Exceptions


logger = logging.getLogger(__name__)
_PASSWORD_HASHER = PasswordHasher()

__all__ = [
    "SimpleSymmetricEncryption",
    "generate_token", "hash_pw", "verify_pw"
]


def generate_token(prefix: str, nbytes: int=32) -> str:
    tok = secrets.token_urlsafe(nbytes=nbytes)
    return f"{prefix}.{tok}"


def hash_pw(password: str) -> str:
    min_len = 16
    if len(password) < min_len:
        raise Exceptions.invalid_parameter("password", password, constraint=f"be at least {min_len} characters")
    return _PASSWORD_HASHER.hash(password)


def verify_pw(*, hash: str, password: str) -> dict:
    try:
        _PASSWORD_HASHER.verify(hash=hash, password=password)
        match = True
    except VerificationError:
        match = False

    try:
        needs_rehash = _PASSWORD_HASHER.check_needs_rehash(hash)
    except InvalidHash:
        needs_rehash = True

    return {
        "match": match,
        "rehash": needs_rehash
    }


class SimpleSymmetricEncryption:
    def __init__(self, key_material: bytes = None, key_cls=Fernet) -> None:
        if key_material is None:
            key_material = Fernet.generate_key()
        self.key = key_cls(key_material)
        self.material = key_material

    @staticmethod
    def canonicalize(*, data: str, account_id: Optional[str]=None) -> str:
        account_id = account_id or "NO_ACCOUNT"
        return f"{account_id}.{data}"

    @staticmethod
    def parse(data: str) -> dict:
        account_id, data = data.split(".", 1)
        if account_id == "NO_ACCOUNT":
            account_id = None
        return {"data": data, "account_id": account_id}

    def encrypt(self, data: str, account_id: Optional[str]=None) -> str:
        to_encrypt = SimpleSymmetricEncryption.canonicalize(data=data, account_id=account_id)
        return self.key.encrypt(to_encrypt.encode()).decode()

    def decrypt(self, data: str, account_id: Optional[str]=None) -> Optional[str]:
        to_parse = self.key.decrypt(data.encode()).decode()
        result = SimpleSymmetricEncryption.parse(to_parse)
        if account_id:
            parsed_account = result["account_id"]
            if not parsed_account or parsed_account != account_id:
                logger.info(f"decrypted account id {parsed_account!r} does not match expected value {account_id!r}")
                return None
        return result["data"]
