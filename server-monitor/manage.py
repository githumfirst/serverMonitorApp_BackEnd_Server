from app import app, db
from flask_migrate import Migrate
from flask_script import Manager

migrate = Migrate(app, db)
manager = Manager(app)

if __name__ == '__main__':
    manager.run()

