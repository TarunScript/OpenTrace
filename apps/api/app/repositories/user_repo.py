"""
User Repository
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.app.models import User
from apps.api.app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, email: str, password: str) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=get_password_hash(password),
            is_verified=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

