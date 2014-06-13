#!/usr/bin/python
import fetcher
import operator
import sys
import time
import Cryptsy


if len(sys.argv) == 2:
    ratio = float(sys.argv[1])
else:
    ratio = 0.3

#conservatively estimate profit with 1% total fees (usually less)
fee_ratio = 0.0025

simpleArb       = []
ltcMarkets      = []
btcMarkets      = []
doubleMarkets   = []
outBuff         = {}
Orders          = {}
runx            = 3


#helper function to format floats
def ff(f):
    return format(f, '.8f')

try:
    print "Fetching market data."
    fetcher.fetchMarketData()
except:
    sys.exit("ERROR: Could not fetch market data.")


print "Processing market data."
for marketName in fetcher.marketData['return']['markets']:
    try:
        lo_sell = fetcher.marketData['return']['markets'][marketName]['sellorders'][0]['price']
        hi_buy  = fetcher.marketData['return']['markets'][marketName]['buyorders'][0]['price']
        sn = fetcher.marketData['return']['markets'][marketName]['primarycode']
        marketid = fetcher.marketData['return']['markets'][marketName]['marketid']
        if hi_buy > lo_sell:
            proft = hi_buy - lo_sell
            simpleArb.append({'profit' : profit, 'market': marketName, 'hi_buy': hi_buy, 'lo_sell': lo_sell, 'sn': sn})
        if fetcher.marketData['return']['markets'][marketName]['secondarycode'] == 'LTC':
            ltcMarkets.append({'market': marketName, 'hi_buy': hi_buy, 'lo_sell': lo_sell, 'sn': sn, 'marketid': marketid})
        if fetcher.marketData['return']['markets'][marketName]['secondarycode'] == 'BTC':
            btcMarkets.append({'market': marketName, 'hi_buy': hi_buy, 'lo_sell': lo_sell, 'sn': sn, 'marketid': marketid})
    except:
        pass

try:
    print "Fetching LTC price."
    ltc_price = float(fetcher.getLTCPrice())
    print("LTC Price: " + format(ltc_price, '.8f')) 
except:
    sys.exit("ERROR: Could not fetch LTC price.")

try:
    print "Fetching balances."
    balances = fetcher.getAvailBalances()
 #   onhold = balances['balances_hold']

   # if fetcher.marketData['return']['markets'][marketName]['secondarycode'] == 'LTC':
#            ltcMarkets.append({'market': marketName, 'hi_buy': hi_buy, 'lo_sell': lo_sell, 'sn': sn, 'marketid': marketid})
    #array of balances
    btc_balance = float(balances['BTC'])
    ltc_balance = float(balances['LTC'])
 #   ltc_hold    = float(onhold['LTC'])
#    btc_hold    = float(onhold['BTC'])
        #rebalancing ltc btc balance
    try:
        if  (ltc_balance) > (btc_balance/ltc_price):
            ltcqtysell = (ltc_balance % (btc_balance / ltc_price))
            c = fetcher.placeOrder(3, 'Sell', ltcqtysell, (ltc_price))
            print (str(c))

    except:
        print("Error: could not balance ltc btc holdings")
    

except:
    print("ERROR: Could not fetch balances.")
    pass 

#check for simple arb opps
for mkt in simpleArb:
    print(mkt['market'] + " : " + mkt['profit'])

#check for ltc -> btc arb opps or btc -> ltc arb opps
print "Processing arbitrage opportunities."
for lmkt in ltcMarkets:
    for bmkt in btcMarkets:
        if lmkt['sn'] == bmkt['sn']:
            print("Checking " + lmkt['sn'] + "...")
            try:
                sn              = lmkt['sn']
                ltc_marketid    = lmkt['marketid']
                btc_marketid    = bmkt['marketid']
                ltc_hi_buy      = float(lmkt['hi_buy'])
                btc_hi_buy      = float(bmkt['hi_buy'])
                ltc_lo_sell     = float(lmkt['lo_sell'])
                btc_lo_sell     = float(bmkt['lo_sell'])
                ltc_hi_buy_btc  = ltc_hi_buy * ltc_price
                ltc_lo_sell_btc = ltc_lo_sell * ltc_price
 #               marketdepth     = depth('marketid')
 #               orders          = marketorders['marketid']

                print("Comparing buy price of " + ff(ltc_lo_sell) + " LTC to sell price of " + ff(btc_hi_buy) + " BTC")
                if btc_hi_buy > ltc_lo_sell_btc:
                    #profit to be made buying for LTC and selling for BTC
                    num_purchasable = (ltc_balance / ltc_lo_sell) * ratio
                    total_fees      = (num_purchasable * ltc_lo_sell) * fee_ratio
                    total_profit    = ((btc_hi_buy - ltc_lo_sell) * num_purchasable) - total_fees
                    print("Calculated total profit: " + ff(total_profit))
                    outstr          = "buy\t" + ff(num_purchasable) + "\t" + sn
                    outstr         += "\t@\t" + ff(ltc_lo_sell) + " LTC"
                    outstr         += "\tsell\t@\t" + ff(btc_hi_buy) + " BTC"
                    outstr         += "\t(" + ff(total_profit) + " BTC profit)? (y/n): "
                    outBuff[total_profit] = {
                        'outstr'            : outstr,
                        'num_purchasable'   : num_purchasable,
                        'buy_marketid'      : ltc_marketid,
                        'sell_marketid'     : btc_marketid,
                        'price buy'         : ff(ltc_lo_sell),
                        'price sell'        : ff(btc_hi_buy)
                    }

                print("Comparing buy price of " + ff(btc_lo_sell) + " BTC to sell price of " + ff(ltc_hi_buy) + " LTC")
                if ltc_hi_buy_btc > btc_lo_sell:
                    #profit to be made buying for BTC and selling for LTC
                    num_purchasable = (btc_balance / btc_lo_sell) * ratio
                    total_fees      = (num_purchasable * btc_lo_sell) * fee_ratio
                    total_profit    = ((ltc_hi_buy_btc - btc_lo_sell) * num_purchasable) - total_fees
                    print("Calculated total profit: " + ff(total_profit))
                    # buy
                    outstr          = "buy\t" + ff(num_purchasable) + "\t" + sn
                    outstr         += "\t@\t" + ff(btc_lo_sell) + " BTC"
                    #sell
                    outstr         += "\tsell\t@\t" + ff(ltc_hi_buy) + " LTC"
                    outstr         += "\t(" + ff(total_profit) + " BTC profit)? (y/n): "
                    outBuff[total_profit] = {
                        'outstr'            : outstr,
                        'num_purchasable'   : num_purchasable,
                        'buy_marketid'      : btc_marketid,
                        'sell_marketid'     : ltc_marketid,
                        'price buy'         : ff(btc_lo_sell),
                        'price sell'        : ff(ltc_hi_buy)
                    }

                print("-----------")

            except:
                pass

sorted_data = sorted(outBuff.iteritems(), key=operator.itemgetter(0), reverse=True)


for (total_profit, data) in sorted_data:
    if data['num_purchasable'] > 0 and total_profit > 0.00000001:
        #currently open buy orders
        buy_market = fetcher.getOrders(data['buy_marketid'])
        #currently open sell orders
        sell_market = fetcher.getOrders(data['sell_marketid'])
        for elem in buy_market:
            print elem 
        for elem in sell_market:
            print elem 
        #kill current buy orders for this market
        try:
            if len(b) > 1:          
                for x in buy_market:
                    cancel = fetcher.cancelOrder
                    terminate = cancel(['orderid'])
                    print (str(terminate))
        except:
            print "No Orders Canceled"
            
        if len(sell_market) < 2 :
            place_order =  raw_input(data['outstr'])
            if place_order == 'y':                 
                r = fetcher.placeOrder(data['buy_marketid'], 'Buy', data['num_purchasable'], data['price buy'])
                print(str(r))
        
                time.sleep(3)
                s = fetcher.placeOrder(data['sell_marketid'], 'Sell', data['num_purchasable'], data['price sell'])
                string = str(s)
                print(string)

                while (s['success']==("0")):
                    time.sleep(3)
                    s = fetcher.placeOrder(data['sell_marketid'], 'Sell', data['num_purchasable'], data['price sell'])
                    print(str(s))
                    
print "Done."

while True:
    execfile("cmd.py")
    




"""orderid   =  allmyOrders.orderid
marketid  =  allmyOrders[2]
#created   =  myOrders['created']
ordertype =  allmyOrders[4]
#quantity  =  myOrders['quantity']


for (orderid) in myOrders():
    if ordertype == 'Buy'& quantity > 0:
        c = fetcher.cancelOrder('orderid')

""""""
"""







""" 
           
            for ordertype
                c = fetcher.cancelAllOrders()
            print("Positions Terminated")

                
            #buyorder = marketorders('buy_marketid')
            #time.sleep(5)"""
    
        
"""try:
    if runx > 0:
        runx = runx - 1
        execfile("cmd.py")"""


