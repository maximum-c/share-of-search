import pandas as pd
from google.oauth2 import service_account
import gspread
from pytrends.request import TrendReq
import requests
import datetime 
from time import sleep
dma_cast_dtype = {'data_feed': 'int64', 
                   'week_of': 'string', 
                   'geoName': 'string',
                   'geoCode': 'int64',
                   'category': 'string',
                   'keywords': 'string',
                   'value': 'int64'}
iot_cast_dtype = {'data_feed' : 'int64',
                  'category': 'string',
                  'keywords': 'string'}
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
def get_datetime_7d():
    date = requests.get('http://worldclockapi.com/api/json/pst/now').json()['currentDateTime']
    date = datetime.datetime.strptime(date.split('T')[0],'%Y-%m-%d') - datetime.timedelta(days=7)
    date = date.strftime('%Y-%m-%d')
    return date
#USER INPUTS
cred_path = str(input("Please provide a filepath to Credential JSON: "))
sheet_name = str(input("Please provide the name of Google sheet: "))

client = gspread.service_account(filename=cred_path)
wks = client.open(sheet_name)
sheet = wks.sheet1
data = sheet.get_all_values()
headers = data.pop(0)
keywords = headers[1:6]
df = pd.DataFrame(data, columns=headers)
df = df.replace('', pd.NA)
df = df.dropna(how='all',subset=keywords)
def kw_extract(n, dataf):
        temp = dataf.iloc[[n]]
        temp = temp.dropna(axis='columns',how='any')
        return temp.values.tolist()[0]
cat_id_arr = df['Category ID'].replace(pd.NA, 0).to_list()
df = df.drop(columns='Category ID')
feed_catg = df[['Data Feed', 'Search Category']].replace(pd.NA, 'All Categories')
df = df.drop(columns=['Data Feed', 'Search Category'])
query_arr = [kw_extract(i,df) for i in df.index]
pytrends = TrendReq(hl='en-US', tz=540, geo='US')

def gtrends_overtime(q_arr, cid_arr, dataf_catg, pytrends):
    i = 0 
    while i < len(cid_arr):
        pytrends.build_payload(q_arr[i], cat=cid_arr[i], timeframe='now 7-d', gprop='')
        #first iteration creates dataframe after each result is concatenated to the end
        if i == 0: 
            df_time = pytrends.interest_over_time()
            #conditional checks to make sure Google Trends returns data else notify slack pass
            if not(df_time.empty):
                df_time['data_feed'] = dataf_catg.iloc[i][0]
                df_time['category'] = dataf_catg.iloc[i][1]
                df_time.drop(columns='isPartial', inplace=True)
                df_time.reset_index(inplace=True)
                #melt to usable format
                output = df_time.melt(id_vars=['date', 'data_feed', 'category'], var_name='keywords')
            else:
                ft_dict = {'date': [pd.NA],
                           'data_feed': [i+1],
                           'category': [dataf_catg.iloc[i][1]],
                           'keywords': ['Lack of Data'],
                           'value': [0]}
                df_time = pd.DataFrame(ft_dict)
                output = df_time
        else:
            df_time = pytrends.interest_over_time()
            #same conditional as above
            if not(df_time.empty):
                df_time['data_feed'] = dataf_catg.iloc[i][0]
                df_time['category'] = dataf_catg.iloc[i][1]
                df_time.drop(columns='isPartial', inplace=True)
                df_time.reset_index(inplace=True)
                #melt to usable format
                df_time = df_time.melt(id_vars=['date','data_feed', 'category'], var_name='keywords')
                output = pd.concat([output, df_time], ignore_index=True)
                
            else:
                ft_dict = {'date': [pd.NA],
                           'data_feed': [i+1],
                           'category': [dataf_catg.iloc[i][1]],
                           'keywords': ['Lack of Data'],
                           'value': [0]}
                df_time = pd.DataFrame(ft_dict)
                output = pd.concat([output, df_time], ignore_index=True)
           
        #arbitrary sleep
        sleep(2)
        i += 1
    output = output.astype(iot_cast_dtype)
    return output

def gtrends_byregion(q_arr, cid_arr, dataf_catg, week_of, pytrends):
    i = 0 
    while i < len(cid_arr):
        pytrends.build_payload(q_arr[i], cid_arr[i], timeframe='now 7-d', gprop='')
        if i == 0:
            df_dma = pytrends.interest_by_region(resolution='DMA', inc_low_vol=True, inc_geo_code=True)
            df_dma['week_of'] = week_of
            df_dma['data_feed'] = dataf_catg.iloc[i][0]
            df_dma['category'] = dataf_catg.iloc[i][1]
            df_dma.reset_index(inplace = True)
            output = df_dma.melt(id_vars=['data_feed','week_of', 'geoName', 'geoCode', 'category'], var_name='keywords')
        else:
            df_dma = pytrends.interest_by_region(resolution='DMA', inc_low_vol=True, inc_geo_code=True)
            df_dma['week_of'] = week_of
            df_dma['data_feed'] = dataf_catg.iloc[i][0]
            df_dma['category'] = dataf_catg.iloc[i][1]
            df_dma.reset_index(inplace = True)
            df_dma = df_dma.melt(id_vars=['data_feed','week_of', 'geoName', 'geoCode', 'category'], var_name='keywords')
            output = pd.concat([output,df_dma], ignore_index=True)
        sleep(2)
        i += 1
    output = output.astype(dma_cast_dtype)
    return output

df_iot = gtrends_overtime(query_arr, cat_id_arr, feed_catg, pytrends)

week = get_datetime_7d()

df_dma = gtrends_byregion(query_arr, cat_id_arr, feed_catg, week, pytrends)

#replace lines below with output of choice below.
df_dma.to_csv(path_or_buf="./dma.csv")
df_iot.to_csv(path_or_buf="./iot.csv")