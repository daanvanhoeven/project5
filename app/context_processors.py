def user_role(request):
    if request.user.is_authenticated and hasattr(request.user, "userprofile"):
        return {
            "role": request.user.userprofile.role
        }
    return {
        "role": None
    }