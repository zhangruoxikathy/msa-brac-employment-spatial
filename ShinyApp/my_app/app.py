# PPHA 30538 Python2
# Fall 2023
# Homework 4

# Kathy Zhang
# zhangruoxikathy

# import packages
from shiny import App, render, ui, reactive
import pandas as pd
import os
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


PATH = r'C:\Users\zhang\GitHub\homework-4-zhangruoxikathy-1'


# prepare data for shiny
def load_file(fname, ftype, skiprows, skipfooter, na_values, remains, yr_str):
    """Read csv and excel files with necessary cleaning steps."""
    """Includes skip rows/footers, identify nas, keep required columns,
    remove spaces in column names, modify year column."""
    if ftype == "csv":
        dfname = pd.read_csv(os.path.join(PATH, fname),
                             skiprows=skiprows,
                             skipfooter=skipfooter,
                             engine='python',
                             na_values=na_values)
    elif ftype == "excel":
        dfname = pd.read_excel(os.path.join(PATH, fname),
                               skiprows=skiprows,
                               skipfooter=skipfooter,
                               na_values=na_values)
    dfname = dfname[remains].copy()

    # remove spaces in column names and make all column names lower-case
    dfname.columns = [c.strip() for c in dfname.columns]
    dfname.columns = dfname.columns.str.lower()

    # make year column into integer-like strings for merging purposes
    if (("year" in dfname.columns) & ("month" in dfname.columns)):
        dfname['year'] = dfname['year'].astype(int)
        dfname['month'] = dfname['month'].astype(int)
        dfname['datetime'] = dfname.apply(lambda row:
                                          datetime.datetime(row['year'],
                                                            row['month'], 1),
                                          axis=1)
    if ("year" in dfname.columns) & (yr_str is True):
        dfname['year'] = dfname['year'].astype(str)

    return dfname


def calculate_share(df, category, share_column):
    """Calculate share of a kind of job among all jobs."""
    df.loc[:, share_column] = df[category] / df['total']
    return df


def fix_na(df, share_column):
    """Manage na data after merge, such as fill with 0, remove placeholders."""
    df.loc[:, share_column] = df[share_column].fillna(0)
    df_new = df.copy()
    df_new.loc[:, share_column] = df_new[share_column].astype(float)
    return df_new


def calculate_share_quantiles(df, share_column, year):
    """Calculate share of a kind of job among all jobs."""
    """And split by quartiles."""
    # filter target year data
    msa_yr = df[df['year'] == year]

    # calculate quartiles for this percentage share column
    msa_yr_wo_zero = msa_yr[msa_yr[share_column] != 0]
    q1 = np.percentile(msa_yr_wo_zero[share_column], 33.33)
    q2 = np.percentile(msa_yr_wo_zero[share_column], 66.67)
    # same as qcut

    def assign_quantile(share):
        """Assign quatiles to each row based on share value."""
        if share == 0:
            return "Zero"
        elif 0 < share <= q1:
            return 'LowestQuantile'
        elif q1 < share <= q2:
            return 'MiddleQuantile'
        elif share > q2:
            return 'TopQuantile'

    msa_yr['quantile'] = msa_yr[share_column].apply(assign_quantile)
    return msa_yr


# run the above functions
# preparing the county-level BEA data
bea = load_file('Table.csv', 'csv', 3, 13, ['(D)', '(NA)'],
                ['GeoFips', 'Description', '2005', '2006', '2007'],
                True)
# preparing the MSA-level BLS data
msa_bls = load_file('ssamatab1.xlsx', 'excel', [0, 1, 3], 5, ['(n)'],
                    ['Area FIPS Code', 'Area', 'Year', 'Month',
                     'Unemployment Rate'], True)
# preparing the county-MSA crosswalk
crosswalk = load_file('geocorr2018_2327800015.csv', 'csv', [1], 0, '-',
                      ['county', 'cbsa10', 'cntyname', 'cbsaname10'], False)

# transform bea into long (tidy) format to be ready for merging
# and add column "total" as sum of manufactuing and military jobs
bea = bea.melt(id_vars=['geofips', 'description'],
               var_name='year', value_name='Value')
bea = bea.pivot(index=['geofips', 'year'], columns='description',
                values='Value').reset_index()
bea.columns = [c.strip() for c in bea.columns]
bea['total'] = bea['Manufacturing'] + bea['Military']
# rename columns to follow style guide
bea.rename(columns={'Manufacturing': 'manufacturing',
                    'Military': 'military',
                    'geofips': 'county_code'}, inplace=True)
bea = bea.dropna()

# rename columns and clean msas for merging purposes
msa_bls.rename(columns={'area': 'msa',
                        'unemployment rate': 'unemployment_rate',
                        'area fips code': 'msa_code'}, inplace=True)
msa_bls_selected = msa_bls[msa_bls['year'].isin(['2005', '2006',
                                                 '2007'])]

# modify county and msa columns to match with the other dataframes
# add comma inbetween state and county to match with msa county column
crosswalk = crosswalk[(crosswalk['cbsaname10'] != '99999')]
crosswalk.rename(columns={'county': 'county_code', 'cntyname': 'county',
                          'cbsaname10': 'msa',
                          'cbsa10': 'msa_code'}, inplace=True)

# inner merge bea and crosswalk first
bea_crosswalk = bea.merge(crosswalk, on='county_code', how='inner')

# aggregate data by msa and year
bea_crosswalk = bea_crosswalk.groupby(['msa_code', 'year'])[['military',
                                                             'manufacturing',
                                                             'total']].sum()
# calculate military and manufacturing shares
bea_crosswalk = calculate_share(bea_crosswalk, 'military', 'Military Share')
bea_crosswalk = calculate_share(bea_crosswalk, 'manufacturing',
                                'Manufacturing Share')

# Merge bea_crosswalk with the newly reshaped bls dataframe so that
# annual jobs and unemployment rate data are categorized in msa-year
bea_bls = bea_crosswalk.merge(msa_bls_selected, on=['msa_code', 'year'],
                              how='right')
bea_bls = fix_na(bea_bls, 'Military Share')
bea_bls = fix_na(bea_bls, 'Manufacturing Share')


# UI components
app_ui = ui.page_fluid(
    ui.row(ui.column(12, ui.h1('Homework 4'),
                     ui.hr(),
                     align='center')),
    ui.layout_sidebar(
        ui.sidebar(ui.h3("Kathy Zhang"),
                   ui.h3('PPHA 30538 Autumn 2023'),
                   ui.output_image(id='logo'),
                   title='Information', gap=5, bg='lightcyan'),
        ui.row(ui.column(4, ui.input_select(id='yr',
                                            label='Please pick a year',
                                            choices=['2005', '2006', '2007']),
                         offset=4),
               ui.column(4, ui.input_select(id='category',
                                            label='Please pick a category',
                                            choices=['manufacturing',
                                                     'military']), offset=4),
               ui.column(4, ui.output_text('if_brac_year'), offset=4)),
        ui.output_plot("plot_quantiles", width='100%'), border_color='black'))


# Server
def server(input, output, session):
    @output
    @render.image
    def logo():
        ofile = "harris logo.png"
        return {'src': ofile, 'contentType': 'image/png'}

    @output
    @render.text
    def if_brac_year():
        if input.yr() == '2005':
            return 'It is a brac year.'
        else:
            return 'It is not a brac year.'

    @reactive.Calc
    def get_column_name():
        share_column = 'Military Share' if input.category() == 'military'\
            else 'Manufacturing Share'
        return share_column

    @reactive.Calc
    def get_yr_name():
        year = input.yr()
        return year

    @output
    @render.table
    def make_table():
        return bea_bls

    @output
    @render.plot(alt="A line plot")
    def plot_quantiles():
        """Graph the quantiles and zero curves for a given year."""
        column = get_column_name()
        year = get_yr_name()
        msa_yr = calculate_share_quantiles(df=bea_bls,
                                           share_column=column,
                                           year=year)
        # create quantile subsets, and then group by months
        # to get the mean unemp rate
        zero = msa_yr[msa_yr['quantile'] == "Zero"]
        low_quant = msa_yr[msa_yr['quantile'] == "LowestQuantile"]
        middle_quant = msa_yr[msa_yr['quantile'] == "MiddleQuantile"]
        top_quant = msa_yr[msa_yr['quantile'] == "TopQuantile"]

        zero_mean = zero.groupby('datetime')['unemployment_rate'].mean()
        low_quant_mean = low_quant.groupby('datetime')['unemployment_rate']\
            .mean()
        middle_quant_mean = middle_quant.groupby('datetime')\
            ['unemployment_rate'].mean()
        top_quant_mean = top_quant.groupby('datetime')['unemployment_rate']\
            .mean()
        # plot the graph for four lines
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(zero_mean.index, zero_mean, 'r-', label='Zero')
        ax.plot(low_quant_mean.index, low_quant_mean, 'y-',
                label='Lowest Quantile')
        ax.plot(middle_quant_mean.index, middle_quant_mean, 'g-',
                label='Middle Quantile')
        ax.plot(top_quant_mean.index, top_quant_mean, 'b-',
                label='Top Quantile')

        # plot BRAC start and end vertical lines with annotations if year=2005
        # get the best vertical position for BRAC start and BRAC end
        text_position = min(pd.concat([zero_mean, low_quant_mean,
                                       middle_quant_mean, top_quant_mean],
                                      ignore_index=True))
        if input.yr() == '2005':
            ax.axvline(pd.to_datetime(f'{input.yr()}-05-01'), color='k',
                       linestyle=':')
            ax.axvline(pd.to_datetime(f'{input.yr()}-09-01'), color='k',
                       linestyle=':')
            ax.annotate(text='BRAC start', xy=(pd.to_datetime('2005-05-01'),
                                               text_position))
            ax.annotate(text='BRAC end', xy=(pd.to_datetime('2005-09-01'),
                                             text_position))

        # format month on the x-axis
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.xticks(rotation=45)

        # add relevant labels and titles
        ax.legend(loc='best')
        ax.set_ylabel('Unemployment rate (%)')
        ax.set_xlabel('Date')
        ax.set_title(f'Average Unemp Rate by {column} Quantiles, {input.yr()}')

        # show graph
        return fig


app = App(app_ui, server, debug=True)
