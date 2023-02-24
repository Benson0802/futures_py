import datetime
import requests
import json
from dateutil.relativedelta import *

class check_opening():
    '''
    檢查開盤時間
    '''
    def __init__(self):
        self.__now = datetime.datetime.now()
        self.__tomorrow = self.__now + datetime.timedelta(days=1)
        self.__day_open = datetime.datetime(self.__now.year, self.__now.month, self.__now.day, 8, 45)
        self.__day_close = datetime.datetime(self.__now.year, self.__now.month, self.__now.day, 13, 45)
        self.__night_open = datetime.datetime(self.__now.year, self.__now.month, self.__now.day, 15, 0)
        self.__night_close = datetime.datetime(self.__tomorrow.year, self.__tomorrow.month, self.__tomorrow.day, 5, 0)
        self.__response = requests.get("https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{0}.json".format(self.__now.year),timeout=60)

    def check_date(self):
        '''
        檢查開盤時間
        '''
        try:
            #排除週日
            if self.__now.weekday() == 6:
                return "周日不開盤"
            #排除週六5:00過後
            if self.__now.weekday() == 5 and self.__now > self.__night_close:
                return "周六五點過後不開盤"
            # #排除平日非開盤時間
            if self.__now < self.__day_open and self.__now > self.__day_close and self.__now < self.__night_open and self.__now > self.__night_close:
                return '平日非開盤時間'
            # #排除國定假日
            if self.__response.status_code == 200:
                data = json.loads(self.__response.text)
                holiday = [item for item in data if item["isHoliday"] is True]
                today = self.__now.date().strftime("%Y%m%d")
                for item in holiday:
                    if item['date'] == today:
                        today = datetime.datetime.now().strftime('%Y-%m-%d')
                        close = datetime.datetime.strptime(today + " 05:00:00", '%Y-%m-%d %H:%M:%S')
                        if(self.__now > close):
                            return '國定假日不開盤'
            return True
        except Exception as err:
            print("An error occurred:", str(err))
            return False
        
    def get_year_mon(self):
        '''
        判斷當月第三週日盤及夜盤取得開盤的年份及月份
        '''
        third_week_date = None
        mon = None
        if(self.__now.month is 12):
            third_week_date = datetime.date(self.__now.year, 12, 1) + relativedelta(day=13, weekday=WE(-1))
            settlement = datetime.datetime.combine(third_week_date, datetime.time(13, 45, 00)).strftime('%Y-%m-%d %H:%M:%S')
            settlement_datetime = datetime.datetime.strptime(settlement, '%Y-%m-%d %H:%M:%S')
            if self.__now.today() > settlement_datetime:
                dict = {'year':self.__now.year+1,'mon':"01"}
            else:
                dict = {'year':self.__now.year,'mon':self.__now.month}
        else:
            today = self.__now.today()
            first_day_of_month = datetime.date(today.year, today.month, 1)
            days_to_wednesday = (2 - first_day_of_month.weekday()) % 7
            first_wednesday = first_day_of_month + datetime.timedelta(days=days_to_wednesday)
            third_wednesday = first_wednesday + datetime.timedelta(weeks=2)
            settlement = datetime.datetime.combine(third_wednesday, datetime.time(13, 45, 00)).strftime('%Y-%m-%d %H:%M:%S')
            settlement_datetime = datetime.datetime.strptime(settlement, '%Y-%m-%d %H:%M:%S')
            if self.__now.today() > settlement_datetime:
                if len((self.__now.month+1).__str__()) is 1:
                    mon = "0" + str(self.__now.month+1)
                else:
                    mon = str(self.__now.month)
                dict = {'year':self.__now.year,'mon':mon}
            else:
                if len((self.__now.month).__str__()) is 1:
                    mon = "0"+ str({self.__now.month})
                else:
                    mon = str(self.__now.month)
                dict = {'year':self.__now.year,'mon':self.__now.month}
        return dict