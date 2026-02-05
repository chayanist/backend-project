from enum import Enum

class MessageEnum(str, Enum):
    SUCCESS = "success"
    CREATED = "create success"
    UPDATED = "update success"
    DELETED = "delete success"

    LOGIN_SUCCESS = "login success"
    INVALID_CREDENTIALS = "invalid username or password"
    USER_NOT_FOUND = "user not found"

    NOT_FOUND = "data not found"
    VALIDATION_ERROR = "validation error"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    SERVER_ERROR = "internal server error"
