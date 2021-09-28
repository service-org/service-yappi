#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import os
import time
import yappi
import tempfile
import typing as t

from logging import getLogger
from service_core.core.context import WorkerContext
from service_yappi.constants import YAPPI_CONFIG_KEY
from service_core.core.service.dependency import Dependency

logger = getLogger(__name__)


class Profiler(Dependency):
    """ Profiler依赖类

    doc: https://github.com/sumerc/yappi
    """

    name = 'Profiler'

    def __init__(
            self,
            alias: t.Text,
            profile_options: t.Optional[t.Dict[t.Text, t.Any]] = None,
            getfunc_options: t.Optional[t.Dict[t.Text, t.Any]] = None,
            **kwargs: t.Any
    ) -> None:
        """ 初始化实例

        @param alias: 配置别名
        @param getfunc_options: 过滤配置
        @param profile_options: 采集配置
        @param kwargs: 其它配置
        """
        self.alias = alias
        self.profile_options = profile_options or {}
        self.getfunc_options = getfunc_options or {}
        super(Profiler, self).__init__(**kwargs)

    def setup(self) -> None:
        """ 生命周期 - 载入阶段

        @return: None
        """
        profile_options = self.container.config.get(f'{YAPPI_CONFIG_KEY}.{self.alias}.profile_options', default={})
        # 防止YAML中声明值为None
        self.profile_options = (profile_options or {}) | self.profile_options
        getfunc_options = self.container.config.get(f'{YAPPI_CONFIG_KEY}.{self.alias}.getfunc_options', default={})
        # 防止YAML中声明值为None
        self.getfunc_options = (getfunc_options or {}) | self.getfunc_options
        # 设置默认的时钟类型为wall
        yappi.set_clock_type('wall')
        # eventlet是基于greenlet
        yappi.set_context_backend('greenlet')

    def worker_setups(self, context: WorkerContext) -> None:
        """ 工作协程 - 载入回调

        @param context: 上下文对象
        @return: None
        """
        yappi.start(**self.profile_options)

    def worker_finish(self, context: WorkerContext) -> None:
        """ 工作协程 - 完毕回调

        @param context: 上下文对象
        @return: None
        """
        yappi.stop()
        ystats = yappi.get_func_stats(**self.getfunc_options)
        pstats = yappi.convert2pstats(ystats)
        base_name = f'{int(time.time() * 1000000)}.prof'
        file_path = os.path.join(tempfile.gettempdir(), 'profile')
        os.path.exists(file_path) or os.makedirs(file_path, exist_ok=True)
        file_name = os.path.join(file_path, base_name)
        pstats.dump_stats(file_name)
        logger.debug(f'dump {base_name} to {file_path} succ')
        yappi.clear_stats()
