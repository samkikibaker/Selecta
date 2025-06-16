from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PlaylistCreateRequest(BaseModel):
    email: EmailStr
    name: str
    songs: list[str]


class PlaylistDeleteRequest(BaseModel):
    email: EmailStr
    name: str


class ReadPlaylistsRequest(BaseModel):
    email: EmailStr
