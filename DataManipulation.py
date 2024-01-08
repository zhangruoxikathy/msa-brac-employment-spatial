# Data Manipulation

###############################################################################
"""
In this .py file, we will clean and merge county-level BEA data and
 MSA-level BLS with light analysis during the BRAC period in the end.
"""
###############################################################################

# import packages
import pandas as pd
import numpy as np
import os


PATH = r'C:\\Users\\zhang\\OneDrive\\Documents\\GitHub'\
    r'\\msa-brac-employment-spatial'


# %% Section 1 Functions

def load_file(fname, ftype, skiprows, skipfooter, na_values, remains, yr_str):
    """Read csv and excel files with necessary cleaning steps."""
    """Includes skip rows, footers, identify n/as, keep required columns,
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
    dfname = dfname[remains]

    # remove spaces in column names and make all column names lower-case
    dfname.columns = [c.strip() for c in dfname.columns]
    dfname.columns = dfname.columns.str.lower()

    # make year column into integer-like strings for merging purposes
    if ("year" in dfname.columns) & (yr_str is True):
        dfname['year'] = (dfname['year'].astype(int)).astype(str)

    return dfname


def clean_names(df, column_name, strings):
    """Replace a list of strings in columns into none."""
    for string in strings:
        df[column_name] = df[column_name].str.replace(string, '', regex=True)


def explore_merge(df):
    """Explore merged df and the _merge column."""
    print(df.dtypes)
    print([df['_merge']])
    print(df[df['_merge'] != 'both'])


def calculate_share_quartiles(df, category, share_column, year, qua_name):
    """Calculate share of a kind of job among all jobs."""
    """And split by quartiles. Apply the quartiles to all years."""
    # calculate share and group df by msa and year, filter base year data
    df[share_column] = df[category]/df['total']
    df_msa_share = df.groupby(['msa', 'year'])['unemployment_rate',
                                               share_column]\
        .mean().reset_index()
    msa_yr_category = df_msa_share[df_msa_share['year'] == year]

    # calculate quartiles for this percentage share column
    q1 = np.percentile(msa_yr_category[share_column], 25)
    q2 = np.percentile(msa_yr_category[share_column], 50)
    q3 = np.percentile(msa_yr_category[share_column], 75)

    def assign_quartile(share):
        """Assign quatiles to each row based on share value."""
        if share <= q1:
            return 'Q1'
        elif q1 < share <= q2:
            return 'Q2'
        elif q2 < share <= q3:
            return 'Q3'
        else:
            return 'Q4'

    msa_yr_category[qua_name] = msa_yr_category[share_column]\
        .apply(assign_quartile)

    # apply base year quartile to the rest of the years
    df_msa_share = msa_yr_category[['msa', qua_name]]\
        .merge(df_msa_share, on='msa', how='inner')

    return df_msa_share


def quartile_unemp_difference(df, category, qua_name, base_year, year_2):
    """Calculate mean unemployment by base_year category share quartile."""
    """For base year and year_2 and their differences."""
    # calculate base year and year 2 mean unemp rates for each quartile
    unemp_q_yr1 = (df[df['year'] == base_year])\
        .groupby([qua_name])['unemployment_rate'].mean().reset_index()
    unemp_q_yr2 = (df[df['year'] == year_2])\
        .groupby([qua_name])['unemployment_rate'].mean().reset_index()

    # find differences in means
    unemp_change = pd.Series(unemp_q_yr2['unemployment_rate'].values
                             - unemp_q_yr1['unemployment_rate'].values,
                             index=['Q1', 'Q2', 'Q3', 'Q4'])
    print(f"""Mean unemployment by {base_year} military share quartile for
          {base_year} is \n""", unemp_q_yr1)
    print(f"""Mean unemployment by {base_year} military share quartile for
          {year_2} is \n""", unemp_q_yr2)
    print(f"""The mean change in the unemployment rate between {base_year} and
          {year_2} for each categorical quartile is the following \n""",
          unemp_change)


# %% Section 2 Data Preparation

# 2. Preparing the county-level BEA data

bea = load_file('Table.csv', 'csv', 3, 13, ['(D)', '(NA)'],
                ['GeoName', 'Description', '2005', '2006', '2007'], False)

# transform bea into long (tidy) format to be ready for merging
# and add column "total" as sum of manufactuing and military jobs
bea = bea.melt(id_vars=['geoname', 'description'],
               var_name='year', value_name='Value')
bea = bea.pivot(index=['geoname', 'year'], columns='description',
                values='Value').reset_index()
bea.columns = [c.strip() for c in bea.columns]
bea['total'] = bea['Manufacturing'] + bea['Military']

# rename columns to follow style guide
bea.rename(columns={'Manufacturing': 'manufacturing',
                    'Military': 'military',
                    'geoname': 'county'}, inplace=True)
bea.head()


# 3. Preparing the MSA-level BLS data

msa_bls = load_file('ssamatab1.xlsx', 'excel', [0, 1, 3], 5, ['(n)'],
                    ['Area', 'Year', 'Month', 'Unemployment Rate'], True)

# rename columns and clean msas for merging purposes
msa_bls.rename(columns={'area': 'msa',
                        'unemployment rate': 'unemployment_rate'},
               inplace=True)
clean_names(msa_bls, 'msa', [' MSA', ' Met NECTA'])


# 4. Preparing the county-MSA crosswalk

crosswalk = load_file('geocorr2018_2327800015.csv', 'csv', [1], 0, '-',
                      ['cbsa10', 'cntyname', 'cbsaname10'], False)
crosswalk = crosswalk[(crosswalk['cbsaname10'] != '99999')]

# modify county and msa columns to match with the other dataframes
# add comma inbetween state and county to match with msa county column
crosswalk['cntyname'] = crosswalk['cntyname'].apply(lambda x:
                                                    x[:-3] + ', ' + x[-2:])
crosswalk.rename(columns={'cntyname': 'county',
                          'cbsaname10': 'msa',
                          'cbsa10': 'fipscode'}, inplace=True)

# use clean_names function created earlier to delete unwanted strings
clean_names(crosswalk, 'msa', [' Metropolitan Statistical Area',
                               ' Micropolitan Statistical Area',
                               ' Metropolitan Statistical',
                               ' Micropolitan Statistical'])


# %% Section 3 Dataset Merging

# 5. Merging

# The two merged dfs are investigated types and _merge using explore_merge func

# Inner merge bea and crosswalk first
bea_crosswalk = bea.merge(crosswalk, on='county', how='inner', indicator=True)
explore_merge(bea_crosswalk)
bea_crosswalk = bea_crosswalk.drop('_merge', axis=1)

# Merge bea_crosswalk with the newly reshaped bls dataframe so that annual
# jobs and unemployment rate data are categorized in area-county
msa_bls_annual = msa_bls.groupby(['msa', 'year'])['unemployment_rate'].mean().reset_index()
bea_bls = bea_crosswalk.merge(msa_bls_annual, on=['msa', 'year'], how='inner',
                              indicator=True)
explore_merge(bea_bls)
bea_bls = bea_bls.drop('_merge', axis=1)
bea_bls.dropna(inplace=True)  # keep rows with only complete data
bea_bls.head()
print("""The merges look fine, with exploration of _merge, there are no
      non-both data""")


# %% Section 4 Exploration

# 6. Basic exploration

# Q: divide each MSA up into one of four quartiles based on the military share
# of total employment in 2005 using calculate_share_quartiles function

military_msa = calculate_share_quartiles(bea_bls, 'military', 'military_share',
                                         '2005', 'qua_mi_2005')

# calculate mean unemployment by 2005 military share quartile for 2005
# and 2006 and print their differences
quartile_unemp_difference(military_msa, "military", 'qua_mi_2005', "2005",
                          "2006")
print("""The military share difference table indicates the MSAs with a higher
      proportion of military employment in 2005 see a greater negative change
      in the unemployment from 2005 to 2006. However, in Q3, the percentage
      changed drops but went back high to ~0.47pp in Q4.""")

# Q: divide each MSA up into one of four quartiles based on the manufacturing
# share of total employment in 2005 using calculate_share_quartiles function
manufacturing_msa = calculate_share_quartiles(bea_bls, 'manufacturing',
                                              'manufacturing_share',
                                              '2005', 'qua_ma_2005')

# calculate mean unemployment by 2005 manufacturing share quartile for 2005
# and 2006 and print their differences
quartile_unemp_difference(manufacturing_msa, "manufacturing", 'qua_ma_2005',
                          "2005", "2006")
print("""The manufacturing share difference indicates the MSAs with a higher
      proportion of military employment in 2005 see a lesser negative change
      in the unemployment from 2005 to 2006. However, in Q3, the percentage
      changed surged but went back low to ~0.27pp in Q4. Overall, it is the
      opposite to the military share changes.""")
