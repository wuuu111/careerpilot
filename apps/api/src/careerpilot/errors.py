from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AppError(Exception):
    error_code: str
    message: str
    status_code: int
    details: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


def not_found(error_code: str, message: str, **details: object) -> AppError:
    return AppError(error_code=error_code, message=message, status_code=404, details=details)


def bad_request(error_code: str, message: str, **details: object) -> AppError:
    return AppError(error_code=error_code, message=message, status_code=400, details=details)


def unauthorized(message: str = "Authentication required.") -> AppError:
    return AppError("UNAUTHORIZED", message, 401, {})


def forbidden(error_code: str, message: str, **details: object) -> AppError:
    return AppError(error_code=error_code, message=message, status_code=403, details=details)
