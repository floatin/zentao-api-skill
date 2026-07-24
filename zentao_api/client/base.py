from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import json
import hashlib
import requests
from pathlib import Path


class BaseClient:
    """Mixin for ZenTaoClient."""
    """禅道 API 客户端（老 API）"""

    def __init__(
        self,
        endpoint: str,
        username: str,
        password: str,
        session_dir: Optional[str] = None,
        auto_save: bool = True,
        auto_load: bool = True,
    ):
        """初始化禅道客户端

        Args:
            endpoint: 禅道地址，如 http://127.0.0.1:8080
            username: 用户名
            password: 密码
            session_dir: Session 存储目录
                - 默认 None: 存储在项目根目录的 .zentao/sessions/
                - 也可指定其他路径
            auto_save: 是否自动保存 Session
            auto_load: 是否自动加载已有 Session
        """
        self.endpoint = endpoint.rstrip("/")
        self.username = username
        self.password = password
        self.auto_save = auto_save
        self.auto_load = auto_load

        # 老 API 配置
        self.old_api_base = self.endpoint
        self.session = None
        self.sid = None

        # Session 存储目录
        if session_dir:
            self.session_dir = Path(session_dir)
        else:
            # 默认存储在项目根目录的 .zentao/sessions/
            self.session_dir = Path(__file__).parent.parent / ".zentao" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self) -> Path:
        """获取 Session 文件路径"""
        key = f"{self.endpoint}:{self.username}"
        key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
        return self.session_dir / f"{key_hash}.json"

    def _save_session(self) -> bool:
        """保存 Session 到文件"""
        try:
            if not self.sid or not self.session:
                return False

            session_file = self._get_session_file()
            data = {
                "endpoint": self.endpoint,
                "username": self.username,
                "sid": self.sid,
                "cookies": self.session.cookies.get_dict(),
            }
            session_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"Session 保存失败：{e}")
            return False

    def _load_session(self) -> bool:
        """从文件加载 Session"""
        try:
            session_file = self._get_session_file()
            if not session_file.exists():
                return False

            data = json.loads(session_file.read_text())

            # 验证 endpoint 和 username 匹配
            if (
                data.get("endpoint") != self.endpoint
                or data.get("username") != self.username
            ):
                return False

            self.sid = data.get("sid")
            self.session = requests.session()
            self.session.cookies.update(data.get("cookies", {}))

            # 验证 Session 是否有效
            if self._validate_session():
                return True
            else:
                self.sid = None
                self.session = None
                return False
        except Exception as e:
            print(f"Session 加载失败：{e}")
            return False

    def _validate_session(self) -> bool:
        """验证 Session 是否有效"""
        try:
            url = f"{self.old_api_base}/user-refresh.html"
            response = self.session.get(url, timeout=10)
            # 如果返回登录页面，说明 Session 无效
            if "登录" in response.text or "login" in response.text.lower():
                return False
            return True
        except Exception:
            return False

    def clear_session(self) -> bool:
        """清除保存的 Session"""
        try:
            session_file = self._get_session_file()
            if session_file.exists():
                session_file.unlink()
            self.sid = None
            self.session = None
            return True
        except Exception as e:
            print(f"Session 清除失败：{e}")
            return False

    # ==================== 认证相关 ====================

    def get_session(self, force_refresh: bool = False) -> Optional[str]:
        """获取 Session

        Args:
            force_refresh: 是否强制刷新 Session

        Returns:
            sessionID 或 None
        """
        # 尝试加载已有 Session
        if not force_refresh and self.auto_load and not self.sid:
            if self._load_session():
                return self.sid

        # 获取新 Session
        try:
            sid_url = f"{self.old_api_base}/api-getSessionID.json"
            response = requests.get(sid_url, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    self.sid = json.loads(result["data"])["sessionID"]

                    # 登录
                    login_url = (
                        f"{self.old_api_base}/user-login.json?zentaosid={self.sid}"
                    )
                    self.session = requests.session()
                    login_data = {
                        "account": self.username,
                        "password": self.password,
                        "keepLogin[]": "on",
                        "referer": f"{self.old_api_base}/my/",
                    }
                    login_response = self.session.post(
                        login_url, data=login_data, timeout=30
                    )
                    if login_response.status_code == 200:
                        login_result = login_response.json()
                        if login_result.get("status") == "success":
                            # 自动保存 Session
                            if self.auto_save:
                                self._save_session()
                            return self.sid
            return None
        except Exception as e:
            print(f"Session 获取异常：{e}")
            return None

    def old_request(
        self, method: str, path: str, data: Optional[Dict] = None
    ) -> Tuple[bool, Any]:
        """老 API 请求"""
        if not self.sid:
            self.get_session()

        if not self.sid:
            return False, "认证失败"

        url = f"{self.old_api_base}/{path.lstrip('/')}"
        if "?" in url:
            url += f"&zentaosid={self.sid}"
        else:
            url += f"?zentaosid={self.sid}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, data=data, timeout=30)
            else:
                return False, f"不支持的方法：{method}"

            if response.status_code == 200:
                try:
                    result = response.json()
                except Exception:
                    try:
                        result = json.loads(response.text)
                    except Exception:
                        result = {"raw": response.text}

                if (
                    result.get("status") == "success"
                    or result.get("result") == "success"
                ):
                    return True, result
                else:
                    return False, result
            else:
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

