from apscheduler.schedulers.background import BackgroundScheduler
from user_profile.views import delete_user_data

class AppScheduler:

    # Schedule Tournament
    def __init__(self):
        pass

    # This scheduler will run once in a day
    delete_user_scheduler = BackgroundScheduler()
    delete_user_scheduler.add_job(delete_user_data, "interval", days=1)
    delete_user_scheduler.start()