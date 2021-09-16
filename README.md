# Share of Search

## Introduction
The Goal of this Project is to provide a tool to acquire temporal Google Trend Data to get an estimate of the Share of Search. 
Share of Search is metric highly correlated with total Market Share, which makes it important to know for any organization. 
For example, if one compares the name of a company to the names of their competitors one can get an idea of this metric. 

## Pytrends

To compare keywords, we use [`pytrends`][1] to iteratively compare lists of up to 5 keywords. `pytrends` is an unofficial API for Google Trends.
Google Trends is an Analytics feature provided by Google to look at Relative Search Volume Trends. Google Trends is not perfect however, to prevent abuse of the system by companies
Google places a hard limit of 5 on the number of Keywords one can compare to eachother. Pytrends returns a Pandas DataFrame. We perform 2 types of requests `pytrends.interest_over_time()` and `pytrends.interest_by_region(...)`. The first call gets interest over time data. `interest_by_region` gets the relative search volume for a set time span in specific region at a specific resolution. We use the resolution `'DMA'` and region `'US'`

## Google Sheets
### Google Sheets API
We get around the 5 Keyword limit by using Google Sheets to do Batching. We request from a Google Spreadsheet with the Google Spreadsheet API to iteratively make Pytrends API calls to get the Trend Data. In order to get access to our sheet we have to share it with a Google service account that is given access to the GSheets API (in this case also GCP). The Google Sheet allows the end user to enter a desired search category in a dropdown menu to check search volume in (if blank, it defaults to `'All Categories'`). Each filled row on the Google Sheet is considered a `Data Feed`

### [Example Spreadsheet](https://docs.google.com/spreadsheets/d/1j0TPffBKwwTioU5e8NGYlQ9Ui1aFmBArozujGx7Ywts/edit?usp=sharing)


## Script

There are two versions of the Share of Search project, one is a script designed to be run locally and the other is designed with orchestration and Automatation in mind. The script is pretty simple, on execution prompting the user to provide an exact `filepath` to a service account credential JSON. The User is then prompted to provide the exact name of the Google Worksheet. Then the script works its magic and returns two CSV files with data from the Last Week in the Working Directory.

## Flow

We use [Prefect Cloud][3] to automate the entire process from extraction to upload. Check out the example [notebook](./Share%20of%20Search) 

## Upload and Storage

We upload the results of the `pytrends` requests to the [Google Big Query][2] data warehouse for safe keeping in the cloud and further processing.

<!-- ## Tableau Visualisation

The included Tableau notebook provides an interactive map to visualize the Data accross the Regions within the United States. The user can select the desired `Data Feed`, and the coresponding data will be filtered for the visualization. We also provide a scrollable pane of stacked bar charts where each bar corresponds to a particular DMA and each section of the bar represents a keywords. Tableau allows us to show the Top keyword per `Data Feed`.-->

## Caveats

All Google Trends data is highly relative, meaning the results will vary even if you only change one keyword in the list. 

## Future Features

- Reduce number of hardcoded Parameters.
- Normalization of results according to a reference keyword
- Flask App to make data entry easier (far future)
- Better timestamps for `pytrends.interest_by_region(...)` requests


[1]:<https://github.com/GeneralMills/pytrends> "Pytrends Github"
[2]:<https://cloud.google.com/bigquery> "Google Big Query Website" 
[3]:<https://www.prefect.io/cloud> "Prefect Website"
