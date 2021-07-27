print('roboforex v1.0 trading strategy generator (aka roboforex optimizer)')
print('Made by Jessie Lesbian')
print('Email: jessielesbian@protonmail.com Reddit: https://www.reddit.com/u/jessielesbian')
print('Jessie Lesbian will NOT be responsible for any losses incurred by roboforex')
print('\ninitializing...')
import sys
import math
import libroboforex as roboforex
if len(sys.argv) >= 3:
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    reverse = '--reverse' in sys.argv
    soft_max_stop_loss = 99
    if '--soft-max-stop-loss' in sys.argv:
        soft_max_stop_loss = min(99, int(sys.argv[sys.argv.index('--soft-max-stop-loss') + 1]))
    time_limit = 0
    if '--time-limit' in sys.argv:
        time_limit = int(sys.argv[sys.argv.index('--time-limit') + 1])
    sma_slow = time_limit * 2
    if '--sma-slow' in sys.argv:
        sma_slow = int(sys.argv[sys.argv.index('--sma-slow') + 1])
    sma_fast = sma_slow / 4
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
    volume_offset = -1
    if '--volume' in sys.argv:
        volume_offset = firstline.index('volume')
    print('loading candlesticks...')
    handle.flush()
    candlesticks = []
    for line in handle:
        try:
            line.index('null')
            continue
        except:
            line = line.rstrip().split(',')
            tup = (float(line[open_offset]), float(line[high_offset]), float(line[low_offset]), float(line[close_offset]))
            volume = 1
            if volume_offset >= 0:
                tup = (*tup, float(line[volume_offset]))
            if volume > 0:
                candlesticks.append(tup)
    open_offset = 0
    high_offset = 1
    low_offset = 2
    close_offset = 3
    if volume_offset >= 0:
        volume_offset = 4
    candlesticks_count = len(candlesticks)
    print('Loaded ' + str(candlesticks_count) + ' candlesticks!')
    print('closing CSV file...')
    handle.close()
    if reverse:
        print('Sorting candlesticks...')
        candlesticks.reverse()
    print('Calculating support and resistance levels...')
    buy_signals = []
    support = candlesticks[0][low_offset]
    resistance = candlesticks[0][high_offset]
    uptrend = candlesticks[1][high_offset] > resistance
    index = 0
    while index < candlesticks_count:
        low = candlesticks[index][low_offset]
        high = candlesticks[index][high_offset]
        buy = False
        sell = False
        if uptrend:
            if low < support:
                uptrend = False
                resistance = support
                support = low
            elif high > resistance:
                support = resistance
                resistance = high
        else:
            if low < support:
                resistance = support
                support = low
            elif high > resistance:
                uptrend = True
                support = resistance
                resistance = high
                if sma_slow == 0:
                    buy_signals.append(index)
                else:
                    matype = roboforex.SimpleMovingAverage
                    if volume_offset == 4:
                        matype = roboforex.VolumeWeightedMovingAverage
                    if matype(sma_fast, index, candlesticks) > matype(sma_slow, index, candlesticks):
                        buy_signals.append(index)
        index += 1
    buy_signals_count = len(buy_signals)
    print('found ' + str(buy_signals_count) + ' buy signals!')
    print('finding optimal trailing stop loss level...')
    stop_loss_ratio_profits = []
    stop_loss_ratio = 0
    last_candlestick = candlesticks_count - 1
    while stop_loss_ratio < soft_max_stop_loss:
        stop_loss_ratio += 1
        print('trying a stop loss ratio of ' + str(stop_loss_ratio) + '%')
        inv_stop_loss = (100 - stop_loss_ratio)
        profit = 0
        for index in buy_signals:
            profit += roboforex.simulateEntry(candlesticks, 65536000, stop_loss_ratio, last_candlestick, time_limit, index)
        if stop_loss_ratio != 1:
            if (float(profit) > max(stop_loss_ratio_profits)) & (float(stop_loss_ratio) == soft_max_stop_loss):
                soft_max_stop_loss = min(99, soft_max_stop_loss + 1)
        stop_loss_ratio_profits.append(profit)
    profitability = max(stop_loss_ratio_profits)
    optimal_stop_loss = stop_loss_ratio_profits.index(profitability) + 1
    print('Optimal stop loss ratio is: ' + str(optimal_stop_loss) + '% (trailing stop loss)')
    profitability = math.floor((profitability / buy_signals_count) * 100)
    inv_stop_loss = 100 - optimal_stop_loss
    print('Finding optimal take profit level...')
    take_profit = 1
    max_take_profit = profitability + optimal_stop_loss
    take_profit_ratio_profits = []
    max_profit_take_profit = 0
    while take_profit < max_take_profit:
        print('trying a take profit ratio of ' + str(take_profit) + '%')
        profit = 0
        for index in buy_signals:
            profit += roboforex.simulateEntry(candlesticks, take_profit, optimal_stop_loss, last_candlestick, time_limit, index)
        take_profit_ratio_profits.append(profit)
        take_profit += 1
        if max_profit_take_profit < profit:
            max_profit_take_profit = profit
            if take_profit == max_take_profit:
                max_take_profit += 1
    profitability = max(take_profit_ratio_profits)
    optimal_take_profit = take_profit_ratio_profits.index(profitability) + 1
    print('Optimal take profit ratio is: ' + str(optimal_take_profit) + '%')
    print('Average profit per trade: ' + str(int(math.floor((100.0 * profitability) / buy_signals_count))) + '% in ' + str(buy_signals_count) + ' buy-sell cycles')
    print('saving trading strategy...')
    handle = open(outputfile, 'w')
    handle.write('\'Trailing stop loss allows roboforex to know when to sell the security\'\n')
    handle.write('\'https://www.investopedia.com/terms/t/trailingstop.asp\'\n')
    handle.write('optimal_stop_loss = ' + str(optimal_stop_loss) + '\n')
    handle.write('\'Take profit allows roboforex to know when to sell the security\'\n')
    handle.write('\'https://www.investopedia.com/terms/t/take-profitorder.asp\'\n')
    handle.write('optimal_take_profit = ' + str(optimal_take_profit) + '\n')
else:
    print('usage: py roboforex-optimize.py [input file] [output file] [extra options]')
    print('example: py roboforex-optimize.py Binance_BTCUSDT_1h.csv bitcoin.py --reverse')
