"""img name for events

Revision ID: 8edfa8519c68
Revises: 1fd75109035f
Create Date: 2020-01-17 17:05:20.477690

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8edfa8519c68'
down_revision = '1fd75109035f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('img_name', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'img_name')
    # ### end Alembic commands ###
