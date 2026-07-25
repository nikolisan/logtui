from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DataclassTypeEnum(Enum):
    LOGENTRY = "logentry"


@dataclass
class LogEntry:
    timestamp: datetime
    module: str
    level: str
    message: str
    start_offset: int


class Mapper:
    @classmethod
    def map(cls, obj, dataclass_type: DataclassTypeEnum) -> LogEntry | None:
        if not isinstance(dataclass_type, DataclassTypeEnum):
            raise TypeError(f"Expected DataclassTypeEnum, got {type(dataclass_type)}")
        if isinstance(obj, str) and dataclass_type == DataclassTypeEnum.LOGENTRY:
            return cls._map_logentry(line=obj)

        return None

    @staticmethod
    def _map_logentry(line: str) -> LogEntry:
        _parts = line.split(" - ")
        timestamp = datetime.strptime(_parts[0], "%Y-%m-%d %H:%M:%S,%f").astimezone()
        module = _parts[1]
        level = _parts[2]
        message = _parts[3]
        start_offset = int(_parts[4])
        return LogEntry(timestamp, module, level, message, start_offset)


mapper = Mapper()
