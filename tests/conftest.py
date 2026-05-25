import pytest
from datetime import date
from app import create_app
from extensions import db as _db
from models import User, Anak


@pytest.fixture(scope='function')
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    return _db


@pytest.fixture(scope='function')
def ibu_user(app, db):
    user = User(
        username='ibu_test',
        nama_lengkap='Ibu Test',
        email='ibu@test.com',
        no_whatsapp='081234567890',
        role='user',
        is_active=True,
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    yield user


@pytest.fixture(scope='function')
def anak_ibu(app, db, ibu_user):
    anak = Anak(
        nama='Anak Test',
        tanggal_lahir=date(2024, 1, 15),
        jenis_kelamin='L',
        nama_ibu='Ibu Test',
        no_hp_ortu='081234567890',
        created_by=ibu_user.id,
    )
    db.session.add(anak)
    db.session.commit()
    yield anak


@pytest.fixture(scope='function')
def portal_client(client, ibu_user):
    client.post('/portal/login', data={
        'email': ibu_user.email,
        'password': 'password123',
    }, follow_redirects=True)
    yield client
