import io
import math
import re
import os

from datetime import datetime

from ctpbee import CtpbeeApi, CtpBee
from ctpbee.constant import ContractData, LogData, TickData, BarData, OrderData, TradeData, PositionData, AccountData, \
    Direction, OrderType


class CallPut:
    def __init__(self):
        self.price = 0
        self.put = None
        self.call = None
        self.pdata = None
        self.cdata = None


class ContractGroup:
    def __init__(self):
        self.contract = None
        self.callput = {}


class Demo(CtpbeeApi):
    def __init__(self, name):
        super().__init__(name)
        self.instrument_set = ["rb2310.SHFE"]
        self.isok = False

        self.contract_groups = {}
        self.valid_contract = ["rb", "RB"]

        contract_list_file = 'file.txt'
        if os.path.isfile(contract_list_file):
            os.remove(contract_list_file)

    def on_contract(self, contract: ContractData):
        """ 处理推送的合约信息 """
        print(contract, "\n")
        with io.open('file.txt', 'a', encoding='utf-8') as f:
            f.write(str(contract.symbol) + "\n")

        if contract.option_underlying == "":

            symbols = re.split(r"([A-Za-z]+)([0-9]+)", contract.symbol)
            # print(symbols)
            if len(symbols) < 2:
                return None
            symbol = symbols[1]

            if symbol in self.valid_contract:
                print("create ", contract.symbol)
                self.contract_groups[contract.symbol] = ContractGroup()
                self.contract_groups[contract.symbol].contract = contract
                self.app.subscribe(contract.symbol)

        else:
            symbol = contract.symbol
            symbol = symbol.replace("-", "")
            parts = re.split(r"([A-Za-z]+)([0-9]+)([A-Za-z]+)([0-9]+)", symbol)
            # print(parts)

            symbol = parts[1] + parts[2]
            direction = parts[3]
            strike_price = parts[4]

            if symbol in self.contract_groups:
                if strike_price not in self.contract_groups[symbol].callput:
                    self.contract_groups[symbol].callput[strike_price] = CallPut()
                if direction == "C":
                    self.contract_groups[symbol].callput[strike_price].call = contract
                    print("create ", symbol)
                    self.app.subscribe(contract.symbol)
                elif direction == "P":
                    self.contract_groups[symbol].callput[strike_price].put = contract
                    print("create ", symbol)
                    self.app.subscribe(contract.symbol)

            # pass

    def on_tick(self, tick: TickData) -> None:
        """ 处理推送的tick """
        print(tick)
        if not self.isok:
            return None
        flag = False
        if tick.local_symbol == self.code:
            self.tickdata = tick
            flag = True

        if tick.local_symbol == self.pcode:
            self.ptickdata = tick
            flag = True

        if tick.local_symbol == self.ccode:
            self.ctickdata = tick
            flag = True
        if flag:
            # self.do_trade()
            pass

    def do_trade(self):

        if self.tickdata is None or self.ptickdata is None or self.ctickdata is None:
            return None

        days = (self.expireday - self.tickdata.datetime).days;

        value = self.ctickdata.last_price - self.ptickdata.last_price + (self.price - self.tickdata.last_price) * (
                math.e ** (-0.03 * days / 252))
        print(value)

        if value > 5 and not self.hold1:
            self.action.buy_open(self.tickdata.last_price, 1, self.tickdata, OrderType.LIMIT)
            self.action.sell_open(self.ctickdata.last_price, 1, self.ctickdata, OrderType.LIMIT)
            self.action.buy_open(self.ptickdata.last_price, 1, self.ptickdata, OrderType.LIMIT)
            self.hold1 = True
            self.app.trader.query_position()
            pass
        elif value < -5 and not self.hold2:
            self.action.sell_open(self.tickdata.last_price, 1, self.tickdata, OrderType.LIMIT)
            self.action.buy_open(self.ctickdata.last_price, 1, self.ctickdata, OrderType.LIMIT)
            self.action.sell_open(self.ptickdata.last_price, 1, self.ptickdata, OrderType.LIMIT)
            self.hold2 = True
            self.app.trader.query_position()
        elif math.fabs(value) < 2:
            print("平仓")
            self.action.buy_close(self.tickdata.last_price, 1, self.tickdata, OrderType.LIMIT)
            self.action.sell_close(self.ctickdata.last_price, 1, self.ctickdata, OrderType.LIMIT)
            self.action.buy_close(self.ptickdata.last_price, 1, self.ptickdata, OrderType.LIMIT)
            self.action.sell_close(self.tickdata.last_price, 1, self.tickdata, OrderType.LIMIT)
            self.action.buy_close(self.ctickdata.last_price, 1, self.ctickdata, OrderType.LIMIT)
            self.action.sell_close(self.ptickdata.last_price, 1, self.ptickdata, OrderType.LIMIT)
            self.app.trader.query_position()
        else:
            pass

    def on_init(self, init):
        if init:
            print("init success")
            self.isok = True
            # self.app.subscribe(self.code)
            # self.app.subscribe(self.pcode)
            # self.app.subscribe(self.ccode)

            self.app.trader.query_position()

    def on_order(self, order: OrderData) -> None:
        """ 报单回报 """
        print(order, "\n")
        pass

    def on_trade(self, trade: TradeData) -> None:
        """ 成交回报 """
        # print(trade, "\n")


    def on_position(self, position: PositionData) -> None:
        """ 处理持仓回报 """
        print(position, "\n")
        # if position.local_symbol == self.code:
        #     if position.volume == 0:
        #         self.hold1 = False
        self.action.cancel_all()
        if position.direction == Direction.LONG:
            self.action.buy_close(math.floor(position.price), position.volume, position, OrderType.LIMIT)

        if position.direction == Direction.SHORT:
            self.action.sell_close(math.ceil(position.price), position.volume, position, OrderType.LIMIT)

    def on_account(self, account: AccountData) -> None:
        """ 处理账户信息 """
        print(account, "\n")
        print()


def letsgo():
    app = CtpBee(name="demo", import_name=__name__, refresh=True)
    # 创建对象
    demo = Demo("test")
    # 添加对象, 你可以继承多个类 然后实例化不同的插件 再载入它, 这些都是极其自由化的操作
    app.add_extension(demo)

    app.config.from_json("config.json")
    app.start(log_output=True)
    # 单独开一个线程来进行查询持仓和账户信息


if __name__ == '__main__':
    letsgo()
