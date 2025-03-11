import datetime
import bcrypt
import jwt

from config_data.config import Config, load_config

settings: Config = load_config(".env")
auth_config = settings.authJWT


def encode_jwt(
        payload: dict,
        private_key: str = auth_config.private_key_path.read_text(),
        algorithm: str = auth_config.algorithm,
        expire_minutes: int = auth_config.access_token_expire_minutes,
        expire_timedelta: datetime.timedelta | None = None
) -> str:
    now = datetime.datetime.utcnow()
    if expire_timedelta is not None:
        expire = now + expire_timedelta
    else:
        expire = now + datetime.timedelta(minutes=expire_minutes)

    to_encode = payload.copy()
    to_encode.update(exp=expire, iat=now)
    encoded = jwt.encode(
        to_encode,
        private_key,
        algorithm=algorithm,
    )
    return encoded


def decode_jwt(
        token: str | bytes,
        public_key: str = auth_config.public_key_path.read_text(),
        algorithm: str = auth_config.algorithm,
) -> dict:
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=[algorithm],
    )
    return decoded


def hash_password(
        password: str,
) -> bytes:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt)


def validate_password(
        password: str,
        hashed_password: bytes,
) -> bool:
    return bcrypt.checkpw(
        password=password.encode(),
        hashed_password=hashed_password,
    )
