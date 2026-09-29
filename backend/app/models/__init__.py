# Importing any model first must load app.db.base (which defines Base and then
# registers every model). Without this, `uvicorn app.main:app` can hit a circular import.
import app.db.base  # noqa: F401
