from app.schemas.user_schema import individual_user


def individual_data(todo: dict):
    creator = todo.get("_creator")
    if isinstance(creator, dict):
        creator = individual_user(creator)
    elif creator is not None:
        creator = str(creator)

    return {
        "_id": str(todo["_id"]),
        "title": todo["title"],
        "description": todo["description"],
        "is_completed": todo["is_completed"],
        "is_deleted": todo["is_deleted"],
        "_creator": creator,
        "createdAt": todo["createdAt"],
        "updatedAt": todo["updatedAt"]
    }


def all_todo(todos):
    return [individual_data(todo) for todo in todos]
