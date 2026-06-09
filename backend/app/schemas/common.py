from pydantic import BaseModel


class TestResult(BaseModel):
    ok: bool
    message: str
