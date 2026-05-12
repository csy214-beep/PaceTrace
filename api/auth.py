"""登录 / 注册 / 用户信息"""
from . import client
from .context import ctx


def login(phone: str, password: str) -> dict:
    """密码登录（密码自动 MD5 哈希）

    成功后 ctx.user 自动填充，token 自动保存。
    """
    pwd_hashed = client.md5(password.strip())
    body = {
        "appVersions": "1.8.5",
        "brand": "Xiaomi",
        "deviceToken": "",
        "deviceType": "1",
        "mobileType": "Mi 10",
        "password": pwd_hashed,
        "sysVersions": "12",
        "userPhone": phone.strip(),
    }
    resp = client.post("v1/auth/login/password", body)
    if resp.get("code") in (200, 10000) and resp.get("response"):
        ctx.save_user(resp["response"])
    return resp


def login_by_token() -> dict:
    """用已保存的 token 重新登录"""
    resp = client.get("v1/auth/login/token")
    if resp.get("code") in (200, 10000) and resp.get("response"):
        ctx.save_user(resp["response"])
    return resp


def get_user_info() -> dict:
    """查询当前用户信息"""
    return client.get("v1/auth/query/token")


def logout():
    """清除本地用户信息"""
    ctx.clear()


def get_schools() -> dict:
    """获取学校列表"""
    return client.get("v1/school/getSchoolSingleInfoList")


def get_student_school_name(student_name: str, register_code: str) -> dict:
    return client.get("v1/auth/getStudentSchoolName", {
        "studentName": student_name, "registerCode": register_code
    })


def register(body: dict) -> dict:
    return client.post("v1/auth/userRegister", body)


def send_sms_register(phone: str) -> dict:
    return client.get("v1/auth/sendSmsForRegister", {"phoneNum": phone})


def send_sms_reset(phone: str) -> dict:
    return client.get("v1/auth/sendSmsForPassWord", {"phoneNum": phone})


def reset_password(body: dict) -> dict:
    return client.post("v1/auth/updateUserPassWord", body)


def change_password(body: dict) -> dict:
    return client.post("v1/auth/update/password", body)


def change_phone(body: dict) -> dict:
    return client.post("v1/auth/update/phone", body)


def update_user_info(params: dict) -> dict:
    return client.post("v1/auth/update/user/info", params)
