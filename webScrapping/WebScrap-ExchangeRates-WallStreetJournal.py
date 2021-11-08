import matplotlib.pyplot as plt
import seaborn as sns
import requests
import re
from bs4 import BeautifulSoup
import json

headers = {
    'authority': 'www.wsj.com',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'XYZ_XYZ',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-gpc': '1',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': 'XYZ-XYZ',
}

response = requests.get('https://www.wsj.com/market-data/currencies/exchangerates', headers=headers)
#print(response)
soup = BeautifulSoup(response.content, features="html")

scriptList = soup.findAll('script')
requiredSoapTag = None

#required html body sub-part
"""
    </head>
    <body>
      <div id = 
      <script>
        window.__STATE    ## this is a string
      </script>        
"""       

# string processing to convert it to json
for ii in scriptList:
    if "mdc_exchangerates" in ii.decode():
        requiredSoapTag = ii

# search for "mdc_exchangerates" substring.
exchangeStr = [_.start() for _ in re.finditer("mdc_exchangerates", requiredSoapTag.decode())]
exchangeStr = exchangeStr[1]
# search for "hash" substring.
hashStr = [_.start() for _ in re.finditer("hash", requiredSoapTag.decode()[exchangeStr:])]
# adjust index
startIndex = exchangeStr+len("mdc_exchangerates")+2
endIndex = hashStr[0]-2

requiredOutputString = "{" + requiredSoapTag.decode()[startIndex: exchangeStr+endIndex] + "}"
#print(requiredOutputString)

# convert str to json
reqJson = json.loads(requiredOutputString)
#print(reqJson)

# convert Json into pandas dataFrame
import pandas as pd
df = pd.DataFrame.from_dict(reqJson, orient="index")


# create dataFrame out of innermost list of dictionaries instead of series/ lists
graphTitle = df['introText']['data']
currentDayValue = df['instruments']
dataFrameCurrentDay = pd.DataFrame(currentDayValue['data'])

# this is a series
#print(type(currentDayValue))
              
previousDayValue = df['instrumentSets']

previousDayValueListDict = []
for element in previousDayValue['data']:
    previousDayValueListDict.extend(element['instruments'])

# create dataFrame out of innermost list of dictionaries instead of using series/ lists
dataFramePreviousDay = pd.DataFrame(previousDayValueListDict)


# list of column names
print(currentDayValue['data'][0].keys())
print(dataFramePreviousDay.columns)


# plotting barGraphs to visualise the data
sns.set_theme(style="whitegrid")

# convert to float or int for plotting.
# ensures forbidden string values added for None value is handled before plotting
dataFrameCurrentDay['currentValueInUSD'] = pd.to_numeric(dataFrameCurrentDay['currentValueInUSD'], errors='coerce')
dataFrameCurrentDay['previousValueInUSD'] = pd.to_numeric(dataFrameCurrentDay['previousValueInUSD'], errors='coerce')
dataFrameCurrentDay['currentValuePerUSD'] = pd.to_numeric(dataFrameCurrentDay['currentValuePerUSD'], errors='coerce')
dataFrameCurrentDay['previousValuePerUSD'] = pd.to_numeric(dataFrameCurrentDay['previousValuePerUSD'], errors='coerce')
dataFrameCurrentDay['percentChangeOneDayValueVsUSD'] = pd.to_numeric(dataFrameCurrentDay['percentChangeOneDayValueVsUSD'], errors='coerce')
dataFrameCurrentDay['percentChangeYTDValueVsUSD'] = pd.to_numeric(dataFrameCurrentDay['percentChangeYTDValueVsUSD'], errors='coerce')

dataFrameCurrentDay = dataFrameCurrentDay.astype({"currency": str, "region": str})

sns.set_style("dark")

# plotting whole of dataFrame
groupedBarPlot = sns.catplot(
    data=dataFrameCurrentDay, kind="bar",
    x="currency", y="currentValuePerUSD", hue="region",
    ci="sd", palette="dark", alpha=0.9, height=10)
groupedBarPlot.despine(left=True)
groupedBarPlot.set_axis_labels("region + currency", "currentValuePerUSD")
plt.title(graphTitle)
plt.show()


# plotting for smaller number of entries
dataFrameChunks = []

for ii in list(set(dataFrameCurrentDay['region'])):
    frames = dataFrameCurrentDay[dataFrameCurrentDay['region'] == ii]
    dataFrameChunks.append(frames.head(2))

reducedDataFrame = pd.concat(dataFrameChunks)
groupedBarPlotReduced = sns.catplot(
    data=reducedDataFrame, kind="bar",
    x="currency", y="currentValuePerUSD", hue="region",
    ci="sd", palette="bright", alpha=1, height=10)

groupedBarPlotReduced.despine(left=True)
groupedBarPlotReduced.set_axis_labels("region + currency", "currentValuePerUSD")
plt.title(graphTitle)
plt.show()
