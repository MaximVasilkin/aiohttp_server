import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name = sq.Column(sq.String(length=50), nullable=False, index=True)
    email = sq.Column(sq.String(length=35), nullable=False, unique=True, index=True)
    password = sq.Column(sq.String(), nullable=False, index=True)
    registration_date = sq.Column(sq.DateTime, default=sq.func.now())

    advertisments = relationship('Advertisment', cascade='all,delete', back_populates='user', lazy='joined')

    def to_dict(self):
        info = {'id': self.id,
                'name': self.name,
                'email': self.email,
                'advertisments_count': len(self.advertisments)}
        return info


class Advertisment(Base):
    __tablename__ = 'advertisments'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    owner_id = sq.Column(sq.Integer, sq.ForeignKey('users.id'), nullable=False)

    title = sq.Column(sq.String(length=70), nullable=False, unique=False)
    description = sq.Column(sq.String(length=500), nullable=False, unique=False)
    created_at = sq.Column(sq.DateTime, default=sq.func.now())

    user = relationship('User', back_populates='advertisments', lazy='selectin')

    def to_dict(self):
        info = {'id': self.id,
                'owner': self.user.to_dict(),
                'title': self.title,
                'description': self.description,
                'created_at': str(self.created_at)}
        return info
