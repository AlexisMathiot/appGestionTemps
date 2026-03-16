from pydantic import BaseModel, EmailStr, field_validator, model_validator


class ForgotPasswordForm(BaseModel):
    email: EmailStr


class ResetPasswordForm(BaseModel):
    password: str
    password_confirm: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordForm":
        if self.password != self.password_confirm:
            raise ValueError("Les mots de passe ne correspondent pas")
        return self


class RegisterForm(BaseModel):
    email: EmailStr
    password: str
    password_confirm: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterForm":
        if self.password != self.password_confirm:
            raise ValueError("Les mots de passe ne correspondent pas")
        return self
