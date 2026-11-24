def individual_user(user: dict):
    return {
        "_id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"],
        "dob": user["dob"],
        "totalTodos": user.get("totalTodos", 0),
        "createdAt": user["createdAt"],
        "updatedAt": user["updatedAt"],
        "is_verified": user.get("is_verified", False),
        "profile_picture": user.get("profile_picture"),
    }

def all_users(users):
    return [individual_user(user) for user in users]
