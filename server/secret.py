from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

# Create an “admin” user with password “secret”
u = User(username="admin", password=generate_password_hash("secret"))
db.session.add(u)
db.session.commit()
print("User created!")
