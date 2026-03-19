import re

from pydantic import BaseModel, field_validator, model_validator


class CategoryCreate(BaseModel):
    name: str
    emoji: str
    color: str
    goal_type: str | None = None
    goal_value: int | None = None

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

    @field_validator("goal_type")
    @classmethod
    def goal_type_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in ("daily", "weekly"):
            raise ValueError("Le type d'objectif doit être 'daily' ou 'weekly'")
        return v

    @field_validator("goal_value", mode="before")
    @classmethod
    def goal_value_coerce(cls, v: int | str | None) -> int | None:
        if v is None or v == "":
            return None
        try:
            val = int(v)
        except (ValueError, TypeError):
            raise ValueError("La valeur de l'objectif doit être un nombre entier")
        if val <= 0:
            raise ValueError("La valeur de l'objectif doit être supérieure à 0")
        if val > 10080:
            raise ValueError("La valeur de l'objectif ne peut pas dépasser 10080 minutes")
        return val

    @model_validator(mode="after")
    def goal_fields_consistent(self) -> "CategoryCreate":
        if (self.goal_type is None) != (self.goal_value is None):
            raise ValueError(
                "Le type et la valeur de l'objectif doivent être définis ensemble ou absents ensemble"
            )
        if self.goal_type == "daily" and self.goal_value is not None and self.goal_value > 1440:
            raise ValueError(
                "Un objectif journalier ne peut pas dépasser 1440 minutes (24h)"
            )
        return self


# CategoryUpdate a les mêmes champs et validations que CategoryCreate
CategoryUpdate = CategoryCreate


class SubCategoryCreate(BaseModel):
    name: str
    emoji: str

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
        if not v:
            raise ValueError("L'emoji est obligatoire")
        if len(v) > 10:
            raise ValueError("L'emoji ne doit pas dépasser 10 caractères")
        return v


SubCategoryUpdate = SubCategoryCreate
