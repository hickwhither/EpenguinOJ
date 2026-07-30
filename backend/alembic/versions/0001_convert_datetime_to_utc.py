"""convert existing naive UTC+7 datetimes to UTC

Revision ID: 0001
Revises:
Create Date: 2026-07-30 14:52:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "mysql":
        op.execute("""
            UPDATE contest
            SET registration_start = DATE_SUB(registration_start, INTERVAL 7 HOUR),
                registration_end = DATE_SUB(registration_end, INTERVAL 7 HOUR),
                start_time = DATE_SUB(start_time, INTERVAL 7 HOUR),
                end_time = DATE_SUB(end_time, INTERVAL 7 HOUR)
            WHERE registration_start IS NOT NULL
                OR registration_end IS NOT NULL
                OR start_time IS NOT NULL
                OR end_time IS NOT NULL
        """)
        op.execute("""
            UPDATE contestregistration
            SET registered_at = DATE_SUB(registered_at, INTERVAL 7 HOUR)
        """)
        op.execute("""
            UPDATE submission
            SET date_created = DATE_SUB(date_created, INTERVAL 7 HOUR),
                judged_date = DATE_SUB(judged_date, INTERVAL 7 HOUR)
        """)
        op.execute("""
            UPDATE `user`
            SET date_joined = DATE_SUB(date_joined, INTERVAL 7 HOUR),
                last_login = DATE_SUB(last_login, INTERVAL 7 HOUR)
        """)
    elif dialect == "sqlite":
        op.execute("""
            UPDATE contest
            SET registration_start = datetime(registration_start, '-7 hours'),
                registration_end = datetime(registration_end, '-7 hours'),
                start_time = datetime(start_time, '-7 hours'),
                end_time = datetime(end_time, '-7 hours')
        """)
        op.execute("""
            UPDATE contestregistration
            SET registered_at = datetime(registered_at, '-7 hours')
        """)
        op.execute("""
            UPDATE submission
            SET date_created = datetime(date_created, '-7 hours'),
                judged_date = datetime(judged_date, '-7 hours')
        """)
        op.execute("""
            UPDATE "user"
            SET date_joined = datetime(date_joined, '-7 hours'),
                last_login = datetime(last_login, '-7 hours')
        """)


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "mysql":
        op.execute("""
            UPDATE contest
            SET registration_start = DATE_ADD(registration_start, INTERVAL 7 HOUR),
                registration_end = DATE_ADD(registration_end, INTERVAL 7 HOUR),
                start_time = DATE_ADD(start_time, INTERVAL 7 HOUR),
                end_time = DATE_ADD(end_time, INTERVAL 7 HOUR)
        """)
        op.execute("""
            UPDATE contestregistration
            SET registered_at = DATE_ADD(registered_at, INTERVAL 7 HOUR)
        """)
        op.execute("""
            UPDATE submission
            SET date_created = DATE_ADD(date_created, INTERVAL 7 HOUR),
                judged_date = DATE_ADD(judged_date, INTERVAL 7 HOUR)
        """)
        op.execute("""
            UPDATE `user`
            SET date_joined = DATE_ADD(date_joined, INTERVAL 7 HOUR),
                last_login = DATE_ADD(last_login, INTERVAL 7 HOUR)
        """)
    elif dialect == "sqlite":
        op.execute("""
            UPDATE contest
            SET registration_start = datetime(registration_start, '+7 hours'),
                registration_end = datetime(registration_end, '+7 hours'),
                start_time = datetime(start_time, '+7 hours'),
                end_time = datetime(end_time, '+7 hours')
        """)
        op.execute("""
            UPDATE contestregistration
            SET registered_at = datetime(registered_at, '+7 hours')
        """)
        op.execute("""
            UPDATE submission
            SET date_created = datetime(date_created, '+7 hours'),
                judged_date = datetime(judged_date, '+7 hours')
        """)
        op.execute("""
            UPDATE "user"
            SET date_joined = datetime(date_joined, '+7 hours'),
                last_login = datetime(last_login, '+7 hours')
        """)
