"""added verification flag for users

Revision ID: 356bc480618b
Revises: 264641c51e52
Create Date: 2020-02-01 08:37:30.410787

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '356bc480618b'
down_revision = '264641c51e52'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('verification', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'verification')
    # ### end Alembic commands ###
