import json
class Logger:
    Id=0
    UserId=0
    LogType=''
    LogMessage=False
    StackTrace=False
    CreatedDate=''
    

    def __init__(self,_Id=0,_UserId=0,_LogType='',_LogMessage='',_StackTrace='',_CreatedDate=''):
        self.Id=_Id
        self.UserId=_UserId
        self.LogType=_LogType
        self.LogMessage=_LogMessage
        self.StackTrace=_StackTrace
        self.CreatedDate=_CreatedDate
        

    def getKeys(self):
        return ['Id','UserId','LogType','LogMessage','StackTrace','CreatedDate']

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def toList(self):
        jsonObj = json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        return json.loads(jsonObj)
	   
    def tableName(self):
        return '[dbo].[Logger]'
