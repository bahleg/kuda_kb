import hashlib


class PassStorage:
    @staticmethod
    def is_user(login, hash):
        users = {('oleg', 'wtf'),('test', 'test')}
        for u in users:
            if u[0] == login and hashlib.md5(u[1]).hexdigest() == hash:

                return True
        return False
