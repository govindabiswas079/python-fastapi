def individual_data(todo):
    return {
        "_id": str(todo["_id"]),
        "title": todo["title"],
        "description": todo["description"],
        "is_completed": todo["is_completed"],
        "is_deleted": todo["is_deleted"],
        "createdAt": todo["createdAt"],
        "updatedAt": todo["updatedAt"]
    }


def all_todo(todos):
    return [individual_data(todo) for todo in todos]
