class passwordModel:
    Password=''
    Salt=''
    def __init__(self,_password,_salt):
        self.Password=_password
        self.Salt=_salt