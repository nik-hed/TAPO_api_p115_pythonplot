import asyncio
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import seaborn as sns
from tapo import ApiClient, EnergyDataInterval
import matplotlib.pyplot as plt




import nest_asyncio
nest_asyncio.apply()


#Set the timeperiod to fetch data from today to 6 months back:
timeperiodstart=datetime.now() - relativedelta(months=6)
start_date = str(timeperiodstart.date())  # input start date
end_date = str(datetime.now().date())  # input end date


month_list = [int(i.strftime("20%y%m"))for i in pd.date_range(start=start_date, end=end_date, freq='MS')]
month_list=pd.DataFrame(month_list,columns=['yearmonth'])



async def main():
    tapo_username = "TAPO_USERNAME"
    tapo_password = "TAPO_PASSWORD"
    ip_address=['IP-Device1','IP-Device2','IP-Device3']
    
    energycons = pd.DataFrame(columns=['yearmonth','energy_usage(kWh)','devicename'])
    
    today = datetime.today()
    
    
    for k in range(0,len(ip_address)):
        
        
        client = ApiClient(tapo_username, tapo_password)
        device = await client.p115(ip_address[k])
        
        #Used to get names of devices:
        device_info = await device.get_device_info()

    
       
        #From https://github.com/mihai-dinculescu/tapo/blob/main/tapo-py/tapo.pyi
        # """Energy data interval."""
        #Monthly = "Monthly" """Monthly interval. `start_date` must be the first day of a year."""
        
        energy_data_monthly_lastyear = await device.get_energy_data(
            EnergyDataInterval.Monthly,
            datetime(today.year-1,1,1),
        )
        
        
        lastyear=pd.DataFrame(energy_data_monthly_lastyear.to_dict()['data'],columns=['energy_usage(kWh)'])
        lastyear['index_column'] = lastyear.index
        lastyear['yearmonth']=int(str(today.year-1)+'01')+lastyear['index_column']
         
        
        lastyear=pd.merge(lastyear,month_list,how='inner',left_on='yearmonth',right_on='yearmonth')
        
        energy_data_monthly_thisyear = await device.get_energy_data(
            EnergyDataInterval.Monthly,
            datetime(today.year, 1, 1),
        )
        
        thisyear=pd.DataFrame(energy_data_monthly_thisyear.to_dict()['data'],columns=['energy_usage(kWh)'])
        thisyear['index_column'] = thisyear.index
        thisyear['yearmonth']=int(str(today.year)+'01')+thisyear['index_column']
         
        
        thisyear=pd.merge(thisyear,month_list,how='inner',left_on='yearmonth',right_on='yearmonth')
       
        fullperiopd=pd.concat([lastyear,thisyear])
        
       
        fullperiopd['devicename']=device_info.to_dict()['nickname']
        
        
        
        energycons=pd.concat([energycons,fullperiopd])
        
        energycons=energycons.drop(columns=['index_column'])
        
       
    
    return energycons
   


if __name__ == "__main__":
    monthlydata=asyncio.run(main())
    
    
    

sns.set_theme(style='whitegrid')
sns.barplot(x="yearmonth",y="energy_usage(kWh)",hue="devicename",data=monthlydata)
plt.legend(bbox_to_anchor=(1.02,1),loc='upper left',borderaxespad=0)

plt.savefig("Energy_usage.png", bbox_inches='tight',dpi = 100)
