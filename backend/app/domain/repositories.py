from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import User, Workspace, WorkspaceMember, WorkspaceRole


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError


class WorkspaceRepository(ABC):
    @abstractmethod
    async def create(self, workspace: Workspace) -> Workspace:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[Workspace]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, workspace: Workspace) -> Workspace:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, workspace_id: UUID) -> None:
        raise NotImplementedError


class WorkspaceMemberRepository(ABC):
    @abstractmethod
    async def add(self, member: WorkspaceMember) -> WorkspaceMember:
        raise NotImplementedError

    @abstractmethod
    async def get(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_workspace(self, workspace_id: UUID) -> list[WorkspaceMember]:
        raise NotImplementedError

    @abstractmethod
    async def update_role(self, workspace_id: UUID, user_id: UUID, role: WorkspaceRole) -> WorkspaceMember:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, workspace_id: UUID, user_id: UUID) -> None:
        raise NotImplementedError
