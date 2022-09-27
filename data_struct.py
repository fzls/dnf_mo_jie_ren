from __future__ import annotations

import json
import os.path
from abc import ABCMeta

from log import logger


class Object:
    def __init__(self, fromDict=None):
        if fromDict is None:
            fromDict = {}
        self.__dict__ = fromDict

    def __str__(self):
        return str(self.__dict__)


# 如果配置的值是dict，可以用ConfigInterface自行实现对应结构，将会自动解析
# 如果配置的值是list/set/tuple，则需要实现ConfigInterface，同时重写auto_update_config，在调用过基类的该函数后，再自行处理这三类结果
class ConfigInterface(metaclass=ABCMeta):
    def auto_update_config(self, raw_config: dict):
        if type(raw_config) is not dict:
            logger.warning(f"raw_config={raw_config} is not dict")
        else:
            for key, val in raw_config.items():
                if hasattr(self, key):
                    attr = getattr(self, key)
                    if isinstance(attr, ConfigInterface):
                        config_field: ConfigInterface = attr
                        config_field.auto_update_config(val)
                    else:
                        setattr(self, key, val)

        # 尝试填充一些数组元素
        self.fill_array_fields(raw_config, self.fields_to_fill())

        # 尝试填充一些字典元素
        self.fill_dict_fields(raw_config, self.dict_fields_to_fill())

        # re: 以后有需求的时候再增加处理set、tuple等

        # 调用可能存在的回调
        self.on_config_update(raw_config)

        # 最终返回自己，方便链式调用
        return self

    def load_from_json_file(self, filepath: str):
        if not os.path.isfile(filepath):
            logger.error(f"未发现配置文件 {filepath}")
            return

        with open(filepath, encoding="utf-8") as f:
            raw_config = json.load(f)

        if type(raw_config) != dict:
            logger.warning(f"raw_config={raw_config} load from {filepath} is not dict")
            return

        return self.auto_update_config(raw_config)

    def save_to_json_file(self, filepath: str, ensure_ascii=False, indent=2):
        with open(filepath, "w", encoding="utf-8") as save_file:
            json.dump(to_raw_type(self), save_file, ensure_ascii=ensure_ascii, indent=indent)

    def fill_array_fields(self, raw_config: dict, fields_to_fill: list[tuple[str, type[ConfigInterface]]]):
        for field_name, field_type in fields_to_fill:
            if field_name in raw_config:
                if raw_config[field_name] is None:
                    setattr(self, field_name, [])
                    continue
                if type(raw_config[field_name]) is list:
                    setattr(
                        self, field_name, [field_type().auto_update_config(item) for item in raw_config[field_name]]
                    )

    def fields_to_fill(self) -> list[tuple[str, type[ConfigInterface]]]:
        return []

    def fill_dict_fields(self, raw_config: dict, fields_to_fill: list[tuple[str, type[ConfigInterface]]]):
        for field_name, field_type in fields_to_fill:
            if field_name in raw_config:
                if raw_config[field_name] is None:
                    setattr(self, field_name, {})
                    continue
                if type(raw_config[field_name]) is dict:
                    setattr(
                        self,
                        field_name,
                        {key: field_type().auto_update_config(val) for key, val in raw_config[field_name].items()},
                    )

    def dict_fields_to_fill(self) -> list[tuple[str, type[ConfigInterface]]]:
        return []

    def on_config_update(self, raw_config: dict):
        return

    def __str__(self):
        return json.dumps(to_raw_type(self), ensure_ascii=False)


def to_raw_type(v):
    if isinstance(v, ConfigInterface):
        return {sk: to_raw_type(sv) for sk, sv in v.__dict__.items()}
    elif isinstance(v, list):
        return list(to_raw_type(sv) for sk, sv in enumerate(v))
    elif isinstance(v, tuple):
        return tuple(to_raw_type(sv) for sk, sv in enumerate(v))
    elif isinstance(v, set):
        return {to_raw_type(sv) for sk, sv in enumerate(v)}
    elif isinstance(v, dict):
        return {sk: to_raw_type(sv) for sk, sv in v.items()}
    else:
        return v


def test():
    class TestSubConfig(ConfigInterface):
        def __init__(self):
            self.val = 0

    class TestConfig(ConfigInterface):
        def __init__(self):
            self.int_val = 0
            self.str_val = ""
            self.bool_val = False
            self.list_int: list[int] = []
            self.list_sub_config: list[TestSubConfig] = []
            self.dict_str_str: dict[str, str] = {}
            self.dict_str_sub_config: dict[str, TestSubConfig] = {}

        def fields_to_fill(self) -> list[tuple[str, type[ConfigInterface]]]:
            return [("list_sub_config", TestSubConfig)]

        def dict_fields_to_fill(self) -> list[tuple[str, type[ConfigInterface]]]:
            return [("dict_str_sub_config", TestSubConfig)]

    test_raw_config = {
        "int_val": 1,
        "str_val": "test",
        "bool_val": True,
        "list_int": [1, 2, 3],
        "list_sub_config": [
            {"val": 1},
            {"val": 2},
            {"val": 3},
        ],
        "dict_str_str": {
            "1": "2",
            "2": "4",
            "3": "6",
        },
        "dict_str_sub_config": {
            "1": {"val": 1},
            "2": {"val": 2},
            "3": {"val": 3},
        },
    }

    test_config = TestConfig().auto_update_config(test_raw_config)

    print(test_raw_config)
    print(test_config)


if __name__ == "__main__":
    test()
