from __future__ import annotations


class AutoEmulatorError(Exception):
    """自動化エンジンに関する汎用例外。"""


class ConfigurationError(AutoEmulatorError):
    """設定の読み込みや検証に失敗した場合に送出する。"""


class EngineRuntimeError(AutoEmulatorError):
    """実行時に回復不能なエラーが発生した場合に送出する。"""
