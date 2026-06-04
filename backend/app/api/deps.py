from fastapi import Request

from app.database import Database
from app.settings import Settings


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings

