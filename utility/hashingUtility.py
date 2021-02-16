import bcrypt
from utility.passwordModel import passwordModel
import base64

class hashingUtility:
    def getHashedPassword(self, password):
        salt = (bcrypt.gensalt())
        hashedPassword = bcrypt.hashpw(password.encode(), salt)
        return passwordModel(hashedPassword, salt)

    def matchHashedPassword(self, oldPassword, salt, newPassword):
        hashedPassword = bcrypt.hashpw(newPassword.encode(), salt.encode())
        if oldPassword.encode() == hashedPassword:
            return True
        else:
            return False
