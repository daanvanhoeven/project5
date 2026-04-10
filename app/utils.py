def user_has_role(user, role):
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.role == role


def heeft_rol(user, rol):
    """
    Controleert of een gebruiker een bepaalde rol heeft.
    Bijvoorbeeld:
    heeft_rol(request.user, "admin")
    """

    return (
        hasattr(user, "userprofile")
        and user.userprofile.role == rol
    )