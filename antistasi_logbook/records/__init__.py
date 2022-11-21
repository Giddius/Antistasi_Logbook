from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_record import BaseRecord
    from .antistasi_records import BaseAntistasiRecord

def get_all_antistasi_record_classes()->set[type["BaseAntistasiRecord"]]:
    from .antistasi_records import ALL_ANTISTASI_RECORD_CLASSES
    return ALL_ANTISTASI_RECORD_CLASSES


def get_all_generic_record_classes()->set[type["BaseRecord"]]:
    from .generic_records import ALL_GENERIC_RECORD_CLASSES
    return ALL_GENERIC_RECORD_CLASSES
