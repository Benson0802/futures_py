import shioaji as sj
import json
from cls.convertK import convertK
from cls.tactics.aisle import aisle
from cls.order import order
import globals
import datetime

# with open('API_KEY.json', 'r') as f:
#     json_data = json.load(f)
#     api = sj.Shioaji()
#     api.login(
#         api_key=json_data['api_key'],
#         secret_key=json_data['secret_key'],
#         contracts_cb=lambda security_type: print(
#             f"{repr(security_type)} fetch done.")
#     )

#     kbars = api.kbars(
#         contract=api.Contracts.Futures.TXF.TXFR1,
#         start='2023-05-08',
#         end='2023-05-13',
#     )
#     ck = convertK(kbars)
#     ck.write_history_1k_bar()
#     ck.convert_k_bar('5Min')
#     ck.convert_k_bar('15Min')
#     ck.convert_k_bar('30Min')
#     ck.convert_k_bar('60Min')
#     ck.convert_day_k_bar()

globals.initialize()
while (True):
    ord = aisle(15685)
    ord.run(60)
    # ord = order(15685)
    # ord.strategy1(60)
