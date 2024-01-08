# msa-brac-employment-spatial
# Exploring Metropolitan Statistical Areas and Employment, with Spatial Visualizations
To read more about what an MSA is, see [this link](https://www.census.gov/programs-surveys/metro-micro/about.html) to the US Census Bureau. 

# Files

### Data Sources and Descriptions ('data' folder)
#### 1. ssamatab.xlsx: Monthly statistics on the levels of the labor force, employment, and unemployment, along with the unemployment rate, for all MSAs in the US, from 1990 to 2023.
Bureau of Labor and Statistics (BLS) website: https://www.bls.gov/lau/metrossa.htm. At the bottom under "Downloadable Data Files" select the ZIP version of Table 1. The extracted file is named ssamatab.xlsx by default.
#### 2. geocorr2018_2327800015.csv: County-MSAs linkage file for crosswalk.
Missouri Census Data Center Geographic Correspondence Engine (MABLE Geocorr) at: https://mcdc.missouri.edu/applications/geocorr2018.html. 
  * In the top window select all US states by holding shift and clicking at the bottom
  * In the left window select "County"
  * In the right window select "Core Based Statistical Area (CBSA)"
  * Leave all other selections at their defaults and click "Run request"
  * Save the CSV document generated at the bottom of the next page, that begins with "geocorr2018_"
#### 3. Table.csv: Annual county employment levels for three years, split by total jobs, manufacturing jobs, and military jobs.
To begin, go to the following Bureau of Economic Analysis (BEA) website: https://www.bea.gov/itable/regional-gdp-and-personal-income. Click on:
  * "Interactive Data Tables" (orange bar)
  * "Personal income and employment by county and metropolitan area"
  * "CAEMP25 Total full-time and part-time employment by industry"
  * Select by NAICS code
  * Select "County"
  * Select "All counties in the U.S."
  * In the "Statistic" window, select "Total employment (number of jobs)", "Manufacturing", and "Military" (hold ctrl to select multiple items)
  * Select the years 2005, 2006, and 2007
  * Click "Download" and select "CSV". The resulting file will be named Table.csv
#### 4. hw2_data.csv: BRAC 2005 Closure and Realignment Impacts by Economic Area, cleaned.
#### 5. MSA and State Shapefile Unzipped Files  ('cb_2018_us_state_5m' and 'tl_2019_us_cbsa' folders):
MSA zip shapefile directly from: https://www2.census.gov/geo/tiger/TIGER2019/CBSA/tl_2019_us_cbsa.zip,
and the state zip shapefiles directly from: https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_5m.zip

### Codes
#### 1. Data Manipulation: Clean and merge county-level BEA data and MSA-level BLS with light analysis during the BRAC period in the end.
#### 2. Visualizations: Visualizes per MSA BRAC 2005 Closure and Realignment Impacts data by year, and produce spatial visualizations, outputs to 'ImagesOutput' folder

### Output Images ('ImagesOutput' folder)
#### 1. plot1: Line plot that shows the average unemplotment rate by BRAC direct changes over time in 2005
#### 2. plot2: Spatial map taht plots non-zero direct effects of BRAC, by continental USA MSA
#### 3. plot3_allstates: Spatial map that plots non-zero direct effects of BRAC, by continental and territory USA MSA
 
### Miscellaneous
#### .gitignore file excludes all shapefile folders and any zip files from being committed to the repo.


# Project Description and Step-by-step Instructions
## 1. Follow 'Data Sources and Descriptions' to download the latest dataset

## 2. Preparing the county-level BEA data
The file Table.csv shows annual county employment levels for three years, split by total jobs, manufacturing jobs, and military jobs. Load it in as a dataframe, cleaning it up and reshaping it to long (tidy) format. In this format, each row should be uniquely identified by a place and a time. The end result has five columns (county, year, manufacturing, military, total).

## 3. Preparing the MSA-level BLS data
The file ssamatab.xlsx has the monthly statistics on the levels of the labor force, employment, and unemployment, along with the unemployment rate, for all MSAs in the US, from 1990 to 2023. Load it in as a dataframe and perform any necessary cleaning. The final result has only four columns (area, year, month, unemployment rate).

## 4. Preparing the county-MSA crosswalk
Our goal is to connect the unemployment rate data from the BLS file to the industry-level data from the BEA file, but we have a (fairly common) problem: these datasets are currently mis-matched by the level of geographic resolution. We cannot directly merge counties into MSAs with our current tools. The solution is called a "crosswalk" - a third dataset that does nothing but connect the matching key in each of the other datasets. Fortunately, MSAs are made up of entire counties, so we can easily find the connecting data we need using MABLE Geocorr. Load the crosswalk (the file named begginning with geocorr2018_) into a third dataframe, dropping all counties that aren't part of an MSA (denoted by 99999 in the cbsaname10 column). The final dataframe has only two columns (the counties and the MSAs).

## 5. Merging
Using these three dataframes, combine them into one long "tidy" dataframe where each row is unique by MSA-year. Attempting this will highlight another mismatch - the BEA data is annual and the BLS data is monthly. There are many ways to "solve" this, or it may even be desired (for example, the annual value could be used as a fixed effect in a monthly frequency pannel), but for now simply aggregate the monthly data to annual using the mean value in a given place. When aggregating from county to MSA level, use the sum (because those values are in levels, not rates). 

## 6. Basic exploration
* Divide each MSA up into one of four quartiles based on the military share of total employment in 2005
* Answer the question, "Did MSAs with a higher proportion of military employment in 2005 see a greater or lesser change in the unemployment rate compared to MSAs with a lower proportion of military employment?" 
* Specifically, what is the mean change in the unemployment rate between 2005 and 2006 for each quartile? The answer prints a Pandas Series that shows the four quartiles, next to the four mean unemployment rate changes.
  * Repeat that question for the manufacturing share of total employment in 2005.

## 7. Data Visualization
## Part 1: Line Plot
__1a)__ Using BLS data (ssamatab1.xlsx), modify the code to work here and to keep the "Area FIPS Code" column. Then, filter the data so only observations for 2005 remain, and create a column of datetime objects.

__1b)__ Load the final csv document of BRAC 2005 Closure and Realignment Impacts by Economic Area. Merge this data with the data created in 1a using the FIPS codes, so each row is unique by MSA, and one new column - 'direct' has been added to the four from the first part. Discard the other columns from the BRAC table (the direct column sums all of the other impact columns into one value).

__1c)__ Create a figure to explore this data. The goal is to create a line graph that has the date on the x-axis, and the unemployment rate on the y-axis.

The graph should have three lines; one for MSAs that had net gains from the 2005 BRAC round, one for MSAs that had net losses, and one for MSAs with no gains or losses. Aggregate the MSA-level data into these three groups using the mean value. Make sure your plot clearly displays the data, including using good axis labels, titles, colors and a legend.  

Add two vertical lines, one in May and one in September. Create annotations on the plot for each line, the first saying "BRAC start" and the second saying "BRAC end". Save your figure as hw3q1.png and commit it with your code.

Finally, apply this analysis to other BRAC rounds (there were in fact four others in 1988, 1991, 1993, and 1995) by generalizing the function so that it could generate the same plot for data from other years, assuming that data was in the same format as the 2005 data.

## Part 2: Choropleth

Our goal now is to create a spatial mapping show the direct affects of BRAC in the US.  To do this, download the MSA Shapefile Zip File directly from:

https://www2.census.gov/geo/tiger/TIGER2019/CBSA/tl_2019_us_cbsa.zip

And the state State shapefiles directly from this link:

https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_5m.zip

Unzip them and load these two shapefiles using geopandas.

Merge the BRAC dataframe created from 1b above (not the version merged with the BLS data) into the MSA shapefile. Unfortunately the shapefiles are using some new FIPS codes, while our BLS and BRAC data have old ones. Use the old_new dictionary to update the BRAC msa fips codes. Once applying it, all of the observations from the BRAC data should merge. Keep only the MSAs in your geodataframe that have data from the BRAC direct affects.

From the state geodataframe, drop all places by NAME that are not part of the continental US (Alaska, Hawaii, territories except Washington DC.

Then plot the states with black edges and a white fill. Add to that figure the MSAs that have BRAC effects, colored by how positive or negative the effect is. Save it as hw3q2.png.

Lastly, instead of dropping Alaska, Hawaii, and Puerto Rico, create a figure that has one large subplot for the continental US, and three smaller subplots, one each for those four locations.  Correctly map the MSA BRAC values onto all four subplots. Save it as hw3q2_allstates.png.

