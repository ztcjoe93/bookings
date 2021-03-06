"""max_capacity to events

Revision ID: bdc62a967043
Revises: 209f39d3e6f1
Create Date: 2020-01-15 19:15:34.326643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bdc62a967043'
down_revision = '209f39d3e6f1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('max_capacity', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'max_capacity')
    # ### end Alembic commands ###
