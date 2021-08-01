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
    support = 0.0
    while index < limit:
        if index >= 0 & index < size:
            support = min(candlesticks[index][2], support)
        index += 1
    return support

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
        if (price < stop_loss_price) | (index == limit_index) | (price > take_profit_level):
            return (1 / purchase_price) * (price - purchase_price)
        else:
            stop_loss_price = max(stop_loss_price, (price * inv_stop_loss) / 100)
            index += 1
