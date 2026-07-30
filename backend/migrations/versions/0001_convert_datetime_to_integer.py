"""Convert datetime columns to integer timestamps

Revision ID: 0001
Revises: 
Create Date: 2026-07-30 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TIMESTAMP_COLUMNS = [
    ("user", "date_joined"),
    ("user", "last_login"),
    ("submission", "date_created"),
    ("submission", "judged_date"),
    ("contest", "start_time"),
    ("contest", "end_time"),
    ("contest", "registration_start"),
    ("contest", "registration_end"),
    ("contestregistration", "registered_at"),
]


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    for table, column in _TIMESTAMP_COLUMNS:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(column, type_=sa.Integer())

        if is_sqlite:
            op.execute(
                sa.text(
                    f"UPDATE {table} SET {column} = "
                    f"CAST(strftime('%s', {column}) AS INTEGER) "
                    f"WHERE {column} IS NOT NULL AND {column} != ''"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE {table} SET {column} = UNIX_TIMESTAMP({column}) "
                    f"WHERE {column} IS NOT NULL"
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    for table, column in _TIMESTAMP_COLUMNS:
        if is_sqlite:
            with op.batch_alter_table(table) as batch_op:
                batch_op.alter_column(column, type_=sa.DateTime())
            op.execute(
                sa.text(
                    f"UPDATE {table} SET {column} = "
                    f"datetime({column}, 'unixepoch') "
                    f"WHERE {column} IS NOT NULL"
                )
            )
        else:
            op.execute(
                sa.text(
                    f"UPDATE {table} SET {column} = FROM_UNIXTIME({column}) "
                    f"WHERE {column} IS NOT NULL"
                )
            )
            with op.batch_alter_table(table) as batch_op:
                batch_op.alter_column(column, type_=sa.DateTime())
