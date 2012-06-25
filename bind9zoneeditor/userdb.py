from passlib.apache import HtpasswdFile


class UserDB():

    def __init__(self, filename):
        self.htpasswd = HtpasswdFile(filename)

    def get_users(self):
        self.htpasswd.get_users()

    def check_password(self, user, password):
        return self.htpasswd.check_password(user, password)
