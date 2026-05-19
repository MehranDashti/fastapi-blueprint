from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import User


class PermissionDeniedError(HTTPException):
    def __init__(self, detail: str = "You do not have permission to perform this action.") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def get_all_permissions(user: User) -> set[str]:
    """
    Return the full set of permissions the user holds.

    This is a stub — implement your own logic here. Common approaches:
    - Read from user.roles (if you add a Role model and relationship)
    - Read from a JWT claim embedded at login
    - Fetch from a DB permission table

    Example with roles:
        return {
            perm.name
            for role in user.roles
            for perm in role.permissions
        } | {perm.name for perm in user.direct_permissions}
    """
    return set()


def can(user: User, permission: str) -> bool:
    return permission in get_all_permissions(user)


def can_any(user: User, *permissions: str) -> bool:
    all_perms = get_all_permissions(user)
    return any(p in all_perms for p in permissions)


def can_all(user: User, *permissions: str) -> bool:
    all_perms = get_all_permissions(user)
    return all(p in all_perms for p in permissions)


def require_permission(*permissions: str) -> Callable:
    """Dependency factory — raises 403 if the user lacks ALL specified permissions."""
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not can_all(current_user, *permissions):
            missing = [p for p in permissions if not can(current_user, p)]
            raise PermissionDeniedError(
                detail=f"Missing required permission(s): {', '.join(missing)}."
            )
        return current_user
    dependency.__name__ = f"require_permission({'|'.join(permissions)})"
    return dependency


def require_any_permission(*permissions: str) -> Callable:
    """Dependency factory — raises 403 if the user lacks ANY of the specified permissions."""
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not can_any(current_user, *permissions):
            raise PermissionDeniedError(
                detail=f"Requires at least one of: {', '.join(permissions)}."
            )
        return current_user
    dependency.__name__ = f"require_any_permission({'|'.join(permissions)})"
    return dependency
