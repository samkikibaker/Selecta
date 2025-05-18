from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class QueueJobRequest(BaseModel):
    email: EmailStr


class PlaylistCreateRequest(BaseModel):
    email: EmailStr
    playlist_name: str
    songs: list[str]

class GetPlaylistsRequest(BaseModel):
    email: EmailStr
