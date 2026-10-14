from typing import Any, Generic, TypeVar

from flask import jsonify
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ApiResponse(Generic[T]):
    @staticmethod
    def success(
        data: T | None = None,
        message: str = "Operación exitosa",
        status_code: int = 200,
    ) -> tuple:
        # Accept both Pydantic models (call .dict()) and plain dicts/lists
        # (use as-is). Without this guard, endpoints that pass a dict would
        # crash with AttributeError.
        if data is None:
            serialized = None
        elif isinstance(data, BaseModel):
            serialized = data.dict()
        else:
            serialized = data
        response = {
            "success": True,
            "message": message,
            "data": serialized,
        }
        return jsonify(response), status_code

    @staticmethod
    def error(
        message: str = "Error en la operación",
        details: Any | None = None,
        status_code: int = 400,
    ) -> tuple:
        response = {"success": False, "message": message, "details": details}
        return jsonify(response), status_code

    @staticmethod
    def list_response(
        items: list,
        total: int,
        page: int = 1,
        per_page: int = 10,
        message: str = "Lista obtenida exitosamente",
    ) -> tuple:
        response = {
            "success": True,
            "message": message,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }
        return jsonify(response), 200
