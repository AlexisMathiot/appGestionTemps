import re

from pydantic import BaseModel, field_validator


class CategoryCreate(BaseModel):
    name: str
    emoji: str
    color: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom est obligatoire")
        if len(v) > 100:
            raise ValueError("Le nom ne doit pas dépasser 100 caractères")
        return v

    @field_validator("emoji")
    @classmethod
    def emoji_valid(cls, v: str) -> str:
        if len(v) > 10:
            raise ValueError("L'emoji ne doit pas dépasser 10 caractères")
        return v

    @field_validator("color")
    @classmethod
    def color_hex_valid(cls, v: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("La couleur doit être au format #RRGGBB")
        return v
