import os
import tempfile

database_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
database_file.close()
os.environ["BLUE_DATABASE_URL"] = f"sqlite:///{database_file.name.replace(os.sep, '/')}"
