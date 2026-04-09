def user_has_role(user, role):
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.role == role
