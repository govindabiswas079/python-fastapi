from app.schemas.user_schema import individual_user


def individual_data(todo: dict):
    return {
        "_id": str(todo["_id"]),
        "title": todo["title"],
        "description": todo["description"],
        "is_completed": todo["is_completed"],
        "is_deleted": todo["is_deleted"],
        "_creator": todo["_creator"] if individual_user(todo.get("_creator")) else None,
        "createdAt": todo["createdAt"],
        "updatedAt": todo["updatedAt"]
    }


def all_todo(todos):
    return [individual_data(todo) for todo in todos]
