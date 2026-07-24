"""禅道 API 客户端包（按资源分模块，向后兼容 ZenTaoClient）。"""
from __future__ import annotations

from .base import BaseClient
from ._legacy import LegacyMixin
from .products import ProductsMixin
from .projects import ProjectsMixin
from .stories import StoriesMixin
from .tasks import TasksMixin
from .bugs import BugsMixin
from .qa import QAMixin
from .releases import ReleasesMixin
from .builds import BuildsMixin
from .plans import PlansMixin
from .writes import WritesMixin

from ._credentials import read_credentials

class ZenTaoClient(BaseClient, LegacyMixin, ProductsMixin, ProjectsMixin, StoriesMixin, TasksMixin, BugsMixin, QAMixin, ReleasesMixin, BuildsMixin, PlansMixin, WritesMixin):
    """禅道 API 客户端（向后兼容门面，由 mixin 组合而成）。"""
    pass

__all__ = ['ZenTaoClient', 'read_credentials']