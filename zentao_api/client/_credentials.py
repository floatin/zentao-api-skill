from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict


def read_credentials() -> Optional[Dict[str, str]]:
    """从 TOOLS.md 读取禅道凭证"""
    tools_path = Path(__file__).parent.parent / "TOOLS.md"

    if not tools_path.exists():
        return None

    content = tools_path.read_text(encoding="utf-8")

    # 查找禅道配置部分
    zentao_section_start = -1
    zentao_section_end = -1

    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "## 禅道 API" in line or "## 禅道" in line:
            zentao_section_start = i
        elif (
            zentao_section_start >= 0
            and line.strip().startswith("## ")
            and zentao_section_start not in [i]
        ):
            zentao_section_end = i
            break

    if zentao_section_start < 0:
        return None

    # 提取禅道配置部分
    if zentao_section_end < 0:
        zentao_section = "\n".join(lines[zentao_section_start:])
    else:
        zentao_section = "\n".join(lines[zentao_section_start:zentao_section_end])

    endpoint = None
    username = None
    password = None

    for line in zentao_section.split("\n"):
        line = line.strip()
        if "API 地址" in line and "：" in line:
            endpoint = line.split("：")[-1].strip().strip("*").strip()
        elif "用户名" in line and "：" in line:
            username = line.split("：")[-1].strip().strip("*").strip()
        elif "密码" in line and "：" in line:
            password = line.split("：")[-1].strip().strip("*").strip()

    if endpoint and username and password:
        return {"endpoint": endpoint, "username": username, "password": password}

    return None

