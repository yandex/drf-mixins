from decimal import ROUND_UP, Decimal
from uuid import uuid4


def files_upload_destination(filename):
    uuid = uuid4().hex
    return f"files/{uuid[0]}/{uuid[:2]}/{uuid}/{filename}"


def count_course_student_price(price: Decimal, paid_percent: int | None) -> int:
    paid_percent = paid_percent if paid_percent is not None else 100
    return int(Decimal(price * paid_percent / 100).quantize(1, rounding=ROUND_UP))
