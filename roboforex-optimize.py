print('roboforex v1.0 trading strategy generator (aka roboforex optimizer)')
print('Made by Jessie Lesbian')
print('Email: jessielesbian@protonmail.com Reddit: https://www.reddit.com/u/jessielesbian')
print('Jessie Lesbian will NOT be responsible for any losses incurred by roboforex')
print('\ninitializing...')
import sys
import math
import libroboforex as roboforex
import bisect
import random
if len(sys.argv) >= 3:
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    reverse = '--reverse' in sys.argv
    probe_rounds = 256
    max_stop_loss = 99
    if '--max-stop-loss' in sys.argv:
        max_stop_loss = min(99, int(sys.argv[sys.argv.index('--soft-max-stop-loss') + 1]))
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
    'Dropping outlier candles: insufficient data'
    stop = candlesticks_count - time_limit
    cached_fast_sma = []
    if volume_offset == 4:
        if sma_fast != 0:
            print('Pre-computing short-term VWMA...')
            index = 0
            while index < candlesticks_count:
                cached_fast_sma.append(roboforex.VolumeWeightedMovingAverage(sma_fast, index, candlesticks))
                index += 1
        cached_slow_sma = []
        if sma_slow != 0:
            print('Pre-computing long-term VWMA...')
            index = 0
            while index < candlesticks_count:
                cached_slow_sma.append(roboforex.VolumeWeightedMovingAverage(sma_slow, index, candlesticks))
                index += 1
    else:
        if sma_fast != 0:
            print('Pre-computing short-term SMA...')
            index = 0
            while index < candlesticks_count:
                cached_fast_sma.append(roboforex.SimpleMovingAverage(sma_fast, index, candlesticks))
                index += 1
        cached_slow_sma = []
        if sma_slow != 0:
            print('Pre-computing long-term SMA...')
            index = 0
            while index < candlesticks_count:
                cached_slow_sma.append(roboforex.SimpleMovingAverage(sma_slow, index, candlesticks))
                index += 1
    donchain_sar = 0
    donchain_indicator = []
    if '--donchain-sar' in sys.argv:
        donchain_sar = int(sys.argv[sys.argv.index('--donchain-sar') + 1])
    elif sma_slow != 0:
        donchain_sar = sma_slow / 2
    else:
        roboforex.require(False, 'Donchain channel duration not specified')
    print('Pre-computing donchain channel indicator...')
    index = 0
    while index < candlesticks_count:
        donchain_current = roboforex.DonchainChannel(donchain_sar, index, candlesticks)
        support = donchain_current[0]
        resistance = donchain_current[2]
        ssi = (resistance - support)
        if ssi != 0:
            ssi = int(math.floor(((candlesticks[index][3] - support) / ssi) * 100))
        else:
            ssi = 0
        donchain_indicator.append((*donchain_current, ssi))
        index += 1
    roboforex.require(sma_fast < donchain_sar < sma_slow, "Slow SMA must be larger than fast SMA")
    print('Emitting buy signals...')
    optimal_stop_loss = []
    last_candlestick = candlesticks_count - 1
    buy_signals = []
    start = max(sma_slow, donchain_sar)
    while len(buy_signals) < 100:
        cache = []
        index = start
        while index < stop:
            if (donchain_indicator[index][3] == len(buy_signals)) & (cached_fast_sma[index] > donchain_current[1] > cached_slow_sma[index]):
                cache.append(index)
            index += 1
        buy_signals.append(cache)
    print('Generating optimal stop loss calculation function...')
    perc = 0
    while perc < 100:
        current_optimal_stop_loss = 0
        current_max_profit = 0 - candlesticks_count
        stop_loss = 1
        ceiling = len(buy_signals[perc]) - 1
        if ceiling > 2:
            ceil2 = min(ceiling, probe_rounds)
            tradepoints = []
            while ceil2 != 0:
                tradepoints.append(buy_signals[perc][random.randint(0, ceiling)])
                ceil2 -= 1
            while stop_loss < max_stop_loss:
                profit = 0
                for tradepoint in tradepoints:
                    profit += roboforex.simulateEntry(candlesticks, 0, stop_loss, last_candlestick, time_limit, tradepoint)
                if profit >= current_max_profit:
                    current_max_profit = profit
                    current_optimal_stop_loss = stop_loss
                stop_loss += 1
        optimal_stop_loss.append(current_optimal_stop_loss)
        perc += 1
    perc = 0
    max_take_profit2 = max(optimal_stop_loss)
    optimal_take_profit = []
    print('Generating optimal take profit calculation function...')
    while perc < 100:
        current_optimal_take_profit = 0
        current_max_profit = 0 - candlesticks_count
        take_profit = 1
        ceiling = len(buy_signals[perc]) - 1
        if ceiling > 2:
            ceil2 = min(ceiling, probe_rounds)
            tradepoints = []
            while ceil2 != 0:
                tradepoints.append(buy_signals[perc][random.randint(0, ceiling)])
                ceil2 -= 1
            max_take_profit = max_take_profit2
            while take_profit < max_take_profit:
                profit = 0
                for tradepoint in tradepoints:
                    profit += roboforex.simulateEntry(candlesticks, take_profit, optimal_stop_loss[ceil2], last_candlestick, time_limit, tradepoint)
                if profit >= current_max_profit:
                    current_max_profit = profit
                    current_optimal_take_profit = take_profit
                    if ((take_profit + 1) == max_take_profit) & (profit > current_max_profit):
                        max_take_profit += 1
                take_profit += 1
        optimal_take_profit.append(current_optimal_take_profit)
        perc += 1
    print('encoding trading strategy...')
    encoded = str({'optimal_stop_loss': optimal_stop_loss, 'optimal_take_profit': optimal_take_profit})
    print('saving trading strategy...')
    handle = open(outputfile, 'w')
    handle.write(encoded)
    handle.flush()
    handle.close()
else:
    print('usage: py roboforex-optimize.py [input file] [output file] [extra options]')
    print('example: py roboforex-optimize.py Binance_BTCUSDT_1h.csv bitcoin.trs --reverse')
