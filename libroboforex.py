import sys
import math
def DonchainResistance(period, offset, candlesticks):
    index = int(math.ceil(offset - period))
    limit = int(math.ceil(index + period))
    size = len(candlesticks)
    resistance = 0.0
    while index < limit:
        if index >= 0 & index < size:
            resistance = max(candlesticks[index][1], resistance)
        index += 1
    return resistance

def DonchainSupport(period, offset, candlesticks):
    index = int(math.ceil(offset - period))
    limit = int(math.ceil(index + period))
    size = len(candlesticks)
    lows = []
    while index < limit:
        if index >= 0 & index < size:
            lows.append(candlesticks[index][2])
        index += 1
    if len(lows) == 0:
        return 0
    else:
        return min(lows)

def DonchainChannel(period, offset, candlesticks):
    support = DonchainSupport(period, offset, candlesticks)
    resistance = DonchainResistance(period, offset, candlesticks)
    return (support, (support + resistance) / 2, resistance)

def SimpleMovingAverage(period, offset, candlesticks):
    index = int(math.ceil(offset - period))
    limit = int(math.ceil(index + period))
    size = len(candlesticks)
    total = 0.0
    count = 0.0
    while index < limit:
        if index >= 0 & index < size:
            count += 1
            total += candlesticks[index][3]
        index += 1
    if count == 0:
        return 0
    else:
        return total / count
def VolumeWeightedMovingAverage(period, offset, candlesticks):
    index = int(math.ceil(offset - period))
    limit = int(math.ceil(index + period))
    size = len(candlesticks)
    total = 0.0
    count = 0.0
    while index < limit:
        if index >= 0 & index < size:
            volume = candlesticks[index][4]
            count += volume
            total += candlesticks[index][3] * volume
        index += 1
    if count == 0:
        return 0
    else:
        return total / count
def simulateEntry(candlesticks, take_profit, stop_loss, last_candlestick, time_limit, index):
    purchase_price = candlesticks[index][3]
    take_profit_level = (purchase_price / 100) * (100 + take_profit)
    inv_stop_loss = (100 - stop_loss)
    stop_loss_price = (purchase_price * inv_stop_loss) / 100
    limit_index = last_candlestick
    if time_limit != 0:
        limit_index = min(limit_index, index + time_limit)
    while True:
        price = candlesticks[index][3]
        if (price < stop_loss_price) | (index == limit_index) | ((price > take_profit_level) & take_profit != 0):
            return (1 / purchase_price) * (price - purchase_price)
        else:
            stop_loss_price = max(stop_loss_price, (price * inv_stop_loss) / 100)
            index += 1
def require(trueorfalse, msgifcrash):
    if not trueorfalse:
        print('RoboForex ran into an error and exited!')
        print('Reason: ' + msgifcrash)
        exit(1)
'Price Data Providers'
class AbstractCandleSource:
    backseek = 0
    def readCandle(self, offset):
        return self.readCandleIMPL(offset - self.backseek)
    def readCandles(self, offset, count):
        offset -= self.backseek
        candles = []
        index = 0
        while index < count:
            candles.append(self.readCandleIMPL(offset + index))
            index += 1
        return candles
    def seekBackward(self, seek):
        self.backseek += seek
    def seekForward(self, seek):
        self.backseek -= seek

    def readCandleIMPL(self, param):
        pass


class MemoryCandleSource(AbstractCandleSource):
    candlesticks = []
    def __init__(self, candlesticks):
        for candlestick in candlesticks:
            self.candlesticks.append(candlestick)
    def ReadCandleIMPL(self, offset):
        require(offset >= 0, 'Negative candlestick index')
        return self.candlesticks[0 - offset]

class AbstractTradingAccount:
    'Balances of the trading account'
    cached_balances = {}
    def getBalanceForIMPL(self, asset):
        pass
    def __init__(self, exchange, core_asset):
        self.exchange = exchange
        self.core_asset = core_asset
    def refreshBalanceFor(self, asset):
        require(asset in self.exchange, 'requested balance rescan for non-existent asset')
        self.cached_balances[asset] = self.getBalanceForIMPL(asset)
    def purgeZeroBalances(self):
        for key in self.cached_balances.keys():
            if self.cached_balances[key] == 0:
                self.cached_balances.pop(key)
    def rescanBalances(self):
        cached_balances = {}
        'Exchanges are just a glorified list of assets'
        for key in self.exchange:
            cached_balances[key] = self.getBalanceForIMPL(key)
        self.cached_balances.clear()
        for key, value in cached_balances:
            self.cached_balances[key] = value
        self.purgeZeroBalances()
'A good ol demo trading account for backtesting'
class InternalDemoTradingAccount(AbstractTradingAccount):
    money_balance = 0
    other_balance = 0
    candle_source = None
    def __init__(self, candlesticks, initial_balance):
        super().__init__(['money', 'other'])
        self.money_balance = initial_balance
        self.candle_source = MemoryCandleSource(candlesticks)
    def getBalanceForIMPL(self, asset):
        if asset == 'money':
            return self.money_balance
        else:
            return self.other_balance
    def seekBackward(self, offset):
        self.candle_source.seekBackward(offset)
    def seekForward(self, offset):
        self.candle_source.seekForward(offset)
    def buyIMPL(self, input):
        require(self.money_balance >= input, 'Insufficient balance in demo trading account')
        self.money_balance -= input
        self.other_balance += input / self.candle_source.readCandle(0)[3]
    def sellIMPL(self, input):
        require(self.other_balance >= input, 'Insufficient balance in demo trading account')
        self.other_balance -= input
        self.money_balance += input * self.candle_source.readCandle(0)[3]
