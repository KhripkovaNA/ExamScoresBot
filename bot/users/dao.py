from bot.dao.base import BaseDAO
from bot.users.models import Users


class UsersDAO(BaseDAO):
    model = Users
