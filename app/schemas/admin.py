from pydantic import BaseModel


class UserRoleUpdate(BaseModel):
    role: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
