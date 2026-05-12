"""应用上下文：全局持有当前登录用户信息和 token。"""
import json
import os

from . import client
from .models import User, RunStandard, OauthToken

_config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".data")
_USER_FILE = os.path.join(_config_dir, ".user")


def _build_user(data: dict) -> User:
    """从 dict 构建 User，自动转换嵌套的 OauthToken"""
    kwargs = {}
    for k, v in data.items():
        if k not in User.__dataclass_fields__:
            continue
        if k == "oauthToken" and isinstance(v, dict):
            kwargs[k] = OauthToken(**v)
        else:
            kwargs[k] = v
    return User(**kwargs)


class AppContext:
    def __init__(self):
        self.user: User = User()
        self.run_standard: RunStandard = RunStandard()
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        self._loaded = True
        if os.path.exists(_USER_FILE):
            try:
                with open(_USER_FILE) as f:
                    data = json.load(f)
                self.user = _build_user(data)
                if self.user.oauthToken:
                    client.set_token(self.user.oauthToken.token)
            except Exception:
                pass

    def save_user(self, user_dict: dict):
        self.user = _build_user(user_dict)
        if self.user.oauthToken:
            client.set_token(self.user.oauthToken.token)
        with open(_USER_FILE, "w") as f:
            json.dump(user_dict, f, ensure_ascii=False, indent=2)

    def clear(self):
        self.user = User()
        self.run_standard = RunStandard()
        client.set_token("")
        if os.path.exists(_USER_FILE):
            os.remove(_USER_FILE)
        token_path = os.path.join(_config_dir, ".token")
        if os.path.exists(token_path):
            os.remove(token_path)


ctx = AppContext()
ctx.load()
