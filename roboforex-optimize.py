import random

print('roboforex v1.0 trading strategy generator (aka roboforex optimizer)')
print('Made by Jessie Lesbian')
print('Email: jessielesbian@protonmail.com Reddit: https://www.reddit.com/u/jessielesbian')
print('Jessie Lesbian will NOT be responsible for any losses incurred by roboforex')
print('\ninitializing...')
import sys
import math
if len(sys.argv) >= 3:
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    reverse = '--reverse' in sys.argv
    soft_max_stop_loss = 99
    if '--soft-max-stop-loss' in sys.argv:
        soft_max_stop_loss = min(99, int(sys.argv[sys.argv.index('--soft-max-stop-loss') + 1]))
    print('opening CSV file...')
    handle = open(inputfile, 'r')
    firstline = ''
    print('finding CSV header...')
    for line in handle:
        if line.find(',') > 0:
            firstline = line.rstrip()
            break
    if firstline == '':
        print('ERROR: invalid CSV header!')
        exit(1)
    print('preparing candlestick parser...')
    firstline = firstline.lower().split(',')
    open_offset = firstline.index('open')
    high_offset = firstline.index('high')
    low_offset = firstline.index('low')
    close_offset = firstline.index('close')

    print('loading candlesticks...')
    handle.flush()
    candlesticks = []
    for line in handle:
        line = line.rstrip().split(',')
        candlesticks.append((float(line[open_offset]), float(line[high_offset]), float(line[low_offset]), float(line[close_offset])))
    open_offset = 0
    high_offset = 1
    low_offset = 2
    close_offset = 3
    candlesticks_count = len(candlesticks)
    print('Loaded ' + str(candlesticks_count) + ' candlesticks!')
    print('closing CSV file...')
    handle.close()
    if reverse:
        print('Sorting candlesticks...')
        candlesticks.reverse()
    print('Calculating support and resistance levels...')
    buy_signals = []
    sell_signals = []
    buy_signal_status = []
    sell_signal_status = []
    support = candlesticks[0][low_offset]
    resistance = candlesticks[0][high_offset]
    uptrend = candlesticks[1][high_offset] > resistance
    trends = []
    index = 0
    while index < candlesticks_count:
        index = len(trends)
        low = candlesticks[index][low_offset]
        high = candlesticks[index][high_offset]
        buy = False
        sell = False
        if uptrend:
            if low < support:
                sell_signals.append(index)
                uptrend = False
                resistance = support
                support = low
                sell = True
            elif high > resistance:
                buy_signals.append(index)
                support = resistance
                resistance = high
                buy = True
        else:
            if low < support:
                sell_signals.append(index)
                resistance = support
                support = low
                sell = True
            elif high > resistance:
                buy_signals.append(index)
                uptrend = True
                support = resistance
                resistance = high
                buy = True
        buy_signal_status.append(buy)
        sell_signal_status.append(sell)
        trends.append((float(support), float(resistance), uptrend))
        index += 1
    buy_signals_count = len(buy_signals)
    sell_signals_count = len(sell_signals)
    print('found ' + str(buy_signals_count) + ' buy signals!')
    print('found ' + str(sell_signals_count) + ' sell signals!')
    print('finding optimal trailing stop loss level...')
    stop_loss_ratio_profits = []
    stop_loss_ratio = 0
    while stop_loss_ratio < soft_max_stop_loss:
        stop_loss_ratio += 1
        print('trying a stop loss ratio of ' + str(stop_loss_ratio) + '%')
        inv_stop_loss = (100 - stop_loss_ratio)
        profit = 0
        for index in buy_signals:
            purchase_price = candlesticks[index][close_offset]
            stop_loss_price = (purchase_price * inv_stop_loss) / 100
            last_candlestick = candlesticks_count - 1
            buy_signal = index
            while index < candlesticks_count:
                price = candlesticks[index][close_offset]
                if (price < stop_loss_price) | (index == last_candlestick):
                    profit += (1 / purchase_price) * (price - purchase_price)
                    break
                stop_loss_price = max(stop_loss_price, (price * inv_stop_loss) / 100)
                index += 1
        if stop_loss_ratio != 1:
            if (float(profit) > max(stop_loss_ratio_profits)) & (float(stop_loss_ratio) == soft_max_stop_loss):
                soft_max_stop_loss = min(99, soft_max_stop_loss + 1)
        stop_loss_ratio_profits.append(profit)
    profitability = max(stop_loss_ratio_profits)
    optimal_stop_loss = stop_loss_ratio_profits.index(profitability) + 1
    print('Optimal stop loss ratio is: ' + str(optimal_stop_loss) + '% (trailing stop loss)')
    profitability = math.floor((profitability / buy_signals_count) * 100)
    print('Average profit per trade: ' + str(profitability) + '% in ' + str(buy_signals_count) + ' buy-sell cycles')
    print('saving trading strategy...')
    handle = open(outputfile, 'w')
    handle.write('\'Trailing stop loss allows roboforex to know when to sell the security\'\n')
    handle.write('\'https://www.investopedia.com/terms/t/trailingstop.asp\'\n')
    handle.write('optimal_stop_loss = ' + str(optimal_stop_loss) + '\n')
else:
    print('usage: py roboforex-optimize.py [input file] [output file] [extra options]')
    print('example: py roboforex-optimize.py Binance_BTCUSDT_1h.csv bitcoin.py --reverse')
