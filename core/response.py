
from core.messages import MessageEnum


def success(data=None, message: MessageEnum = MessageEnum.SUCCESS):
    return {
        "status": "success",
        "message": message,
        "data": data
    }

def error(message: MessageEnum, data=None):
    return {
        "status": "error",
        "message": message,
        "data": data
    }