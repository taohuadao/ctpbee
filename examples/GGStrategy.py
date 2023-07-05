import math
from datetime import datetime

from ctpbee import CtpbeeApi, CtpBee
from ctpbee.constant import ContractData, LogData, TickData, BarData, OrderData, TradeData, PositionData, AccountData, \
    Direction, OrderType


class Demo(CtpbeeApi):
    def __init__(self, name, code, pcode, ccode, price, expireday):
        super().__init__(name)
        self.instrument_set = ["rb2310.SHFE"]
        self.isok = False
        self.code = code
        self.pcode = pcode
        self.ccode = ccode
        self.price = price
        self.expireday = expireday
        self.tickdata = None
        self.ptickdata = None
        self.ctickdata = None

        self.hold1 = False;
        self.hold2 = False;

    def on_contract(self, contract: ContractData):
        """ 处理推送的合约信息 """
        # print(contract, "\n")

    def on_tick(self, tick: TickData) -> None:
        """ 处理推送的tick """
        # print(tick)
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
            self.app.subscribe(self.code)
            self.app.subscribe(self.pcode)
            self.app.subscribe(self.ccode)

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
            self.action.sell_close(math.ceil(position.price) , position.volume, position, OrderType.LIMIT)

    def on_account(self, account: AccountData) -> None:
        """ 处理账户信息 """
        print(account, "\n")


def letsgo():
    app = CtpBee(name="demo", import_name=__name__, refresh=True)
    # 创建对象
    demo = Demo("test", "rb2310.SHFE", "rb2310P4000.SHFE", "rb2310C4000.SHFE", 4000, datetime(2023, 9, 22))
    # 添加对象, 你可以继承多个类 然后实例化不同的插件 再载入它, 这些都是极其自由化的操作
    app.add_extension(demo)

    app.config.from_json("config.json")
    app.start(log_output=True)
    # 单独开一个线程来进行查询持仓和账户信息


if __name__ == '__main__':
    letsgo()
