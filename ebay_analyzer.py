# File: ebaySniper.py
# Author : Vincent Fedetz
# What it does: Determine the lowest BiN for a card
# Select active auctions currently less than lowest BiN -20%
# Select the auction ending soonest

import sys
from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping

#################### Configs ############################
myAppId = 'VincentF-myFirstP-PRD-4668815a4-0c0c2351'
keywords = 'teferi hero'
exclude_keywords = " -emblem -box -playmat -MP -damaged -sleeves -repack -repacks -\"planeswalker packs\" -\"planeswalker pack\"" #need leading space
keywords = keywords + exclude_keywords
category = '19107'  # MTG Category ID = 19107
zip_code = '19711'

#################### API Wrappers #######################

def getSingleItem(itemId):
    api = Shopping(appid=myAppId, config_file=None)
    response = api.execute('GetSingleItem', {
       'itemID': itemId
    })
    return response.dict()
    
def getShippingCost(itemId):
    api = Shopping(appid=myAppId, config_file=None)
    response = api.execute('GetShippingCosts', {
       'itemID': itemId,
       'DestinationPostalCode': '19711'
    })
    return response.dict()

def findItemsAdvanced(keywords):
    api = Finding(appid=myAppId, config_file=None)
    response = api.execute('findItemsAdvanced', {
        'keywords': keywords,
        'categoryId': category,
        'sortOrder': 'PricePlusShippingLowest'
    })
    return response.dict()
    
################### Data Crunching Functions ############ 

def findAllBINItems(keywords):
    sys.stdout.write( 'Finding Lowest Buy it Now Price' )
    sys.stdout.flush()

    resDict = findItemsAdvanced(keywords)
    myDict = {}
    
    for item in resDict['searchResult']['item']:
        itemID = item['itemId']
        listing_type = item['listingInfo']['listingType']
        
        if (listing_type == 'AuctionWithBIN'):
            itemDict = getSingleItem(itemID)
            item_cost = itemDict['Item']['ConvertedBuyItNowPrice']['value']
        
        elif (listing_type == 'FixedPrice'):
            item_cost = item['sellingStatus']['convertedCurrentPrice']['value']
        
        else:
            continue
    
        shipDict = getShippingCost(itemID)
        ship_cost = shipDict['ShippingCostSummary']['ListedShippingServiceCost']['value']

        total_cost = float(item_cost) + float(ship_cost)
        myDict[itemID] = {
            'title': item['title'].encode('utf-8').strip(),
            'item_cost': item_cost,
            'ship_cost': ship_cost,
            'total_cost': total_cost,
            'url': item['viewItemURL']
        }
        sys.stdout.write( '.' )
        sys.stdout.flush()

    print('\n')
    return myDict
    
def findLowestBINPrice(keywords):
    itemDict = findAllBINItems(keywords)
    min_cost = 99999999
    min_cost_item = None
    for i in itemDict:
        if (itemDict[i]['total_cost'] < min_cost):
            min_cost = itemDict[i]['total_cost']
            min_cost_item = itemDict[i]
    return min_cost_item
    
def findReasonableAuctions(keywords, target_price):
    print 'Finding Reasonable Auctions < $', target_price
    sys.stdout.flush()
    
    resDict = findItemsAdvanced(keywords)
    myDict = {}
    
    for item in resDict['searchResult']['item']:
        itemId = item['itemId']
        listing_type = item['listingInfo']['listingType']
        
        if (listing_type == 'Auction'):
            item_cost = float(item['sellingStatus']['convertedCurrentPrice']['value'])
        
        elif (listing_type == 'AuctionWithBIN'):
            itemDict = getSingleItem(itemId)
            item_cost = float(itemDict['Item']['ConvertedBuyItNowPrice']['value'])
        
        else:
            continue
        
        if (item_cost < target_price):
            shipDict = getShippingCost(itemId)
            ship_cost = float(shipDict['ShippingCostSummary']['ListedShippingServiceCost']['value'])
            total_cost = item_cost + ship_cost
            
            if (total_cost + ship_cost < target_price):
                myDict[itemId] = {
                    'title': item['title'].encode('utf-8').strip(),
                    'item_cost': item_cost,
                    'ship_cost': ship_cost,
                    'total_cost': total_cost,
                    'url': item['viewItemURL'],
                    'end_time': item['listingInfo']['endTime']
                }
                sys.stdout.write( '.' )
                sys.stdout.flush()
    print('\n')
    return myDict
        
def endingSoonest(aucDict):
    soonest_item = None
    soonest = None
    for i in aucDict:
        if (soonest == None):
            soonest = aucDict[i]['end_time']            
        elif (aucDict[i]['end_time'] < soonest):
            soonest = aucDict[i]['end_time']
            soonest_item = aucDict[i]
    return soonest_item

############## Main Commands ######################
binLow = findLowestBINPrice(keywords)
target_price = binLow['total_cost']*.8
print "Target Price =", target_price
aucDict = findReasonableAuctions(keywords,target_price)
print "Target Aquired:", endingSoonest(aucDict)
###################################################
