# Visualizations

###############################################################################
"""
In this .py file, we will visualize per MSA BRAC 2005 Closure and Realignment
 Impacts data by year, and produce spatial visualizations.
"""
###############################################################################

# import packages
import os
import pandas as pd
import datetime
import geopandas
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import make_axes_locatable


PATH = r'C:\\Users\\zhang\\OneDrive\\Documents\\GitHub'\
    r'\\msa-brac-employment-spatial'
IMAGEPATH = r'C:\\Users\\zhang\\OneDrive\\Documents\\GitHub'\
    r'\\msa-brac-employment-spatial\\ImagesOutput'


# %% Section 1 Line Plots

# %%% Sub-Section 1a

def load_file(fname, ftype, skiprows, skipfooter, na_values, remains):
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

    return dfname


def modify_file(fname, year):
    """Modify the file to fit this assignment for visualizations."""
    # keep only data from the wanted year
    new_fname = fname[fname['year'] == year]
    # create datetime column as a combination of year and first day of month
    new_fname['datetime'] = new_fname.apply(lambda row:
                                            datetime.datetime(row['year'],
                                                              row['month'], 1),
                                            axis=1)
    # drop year and month columns after datetime column has been generated
    columns_to_drop = ['year', 'month']
    new_fname = new_fname.drop(columns=columns_to_drop)
    new_fname = new_fname.reset_index(drop=True)
    return new_fname


# load and modyft msa_blas file
msa_bls = load_file('ssamatab1.xlsx', 'excel', [0, 1, 3], 5, ['(n)'],
                    ['Area FIPS Code', 'Area', 'Year', 'Month',
                     'Unemployment Rate'])
msa_bls_new = modify_file(msa_bls, 2005)


# %%% Sub-Section 1b

# load brac file
brac = load_file('hw2_data.csv', 'csv', [], 0, '-', ['direct', 'msa_fips'])


def group_and_merge(file, columnindex_for_merge):
    """Group by msa_fips and sum direct for each msa, then merge."""
    # find sum of direct per msa
    file = file.dropna(subset=['msa_fips'])
    brac_sum = pd.DataFrame(file.groupby('msa_fips')['direct'].sum())
    # merge the new brac sum with msa_bls
    brac_sum[columnindex_for_merge] = brac_sum.index
    merged = brac_sum.merge(msa_bls_new, on=columnindex_for_merge,
                            how='right')
    # find the no change msas
    merged['direct'] = merged['direct'].fillna(0)
    return brac_sum, merged


# get brac_new by msa and merged file of unemployment rate and direct
brac_new, merged_file = group_and_merge(brac, 'area fips code')


# %%% Sub-Section 1c

def plot_gains_losses(file, year):
    """Graph the gains, losses, no gains losses curves for a given year."""
    # create gains, losses, no gains losses subsets, and then group by months
    # to get the mean unemp rate
    gains = file[merged_file['direct'] > 0]
    losses = file[file['direct'] < 0]
    no_gains_losses = file[file['direct'] == 0]
    gains_mean = gains.groupby('datetime')['unemployment rate'].mean()
    losses_mean = losses.groupby('datetime')['unemployment rate'].mean()
    no_gains_losses_mean = no_gains_losses\
        .groupby('datetime')['unemployment rate'].mean()

    # get the best vertical position for BRAC start and BRAC end
    text_position = min(pd.concat([gains_mean, losses_mean,
                                   no_gains_losses_mean], ignore_index=True))

    # plot the graph for three lines
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(gains_mean.index, gains_mean, 'g-', label='net gains')
    ax.plot(losses_mean.index, losses_mean, 'r-', label='net losses')
    ax.plot(no_gains_losses_mean.index, no_gains_losses_mean, 'b-',
            label='no gains or losses')

    # plot BRAC start and end vertical lines with annotations
    ax.axvline(pd.to_datetime(f'{year}-05-01'), color='k', linestyle=':')
    ax.axvline(pd.to_datetime(f'{year}-09-01'), color='k', linestyle=':')
    ax.annotate(text='BRAC start', xy=(pd.to_datetime(f'{year}-05-01'),
                                       text_position))
    ax.annotate(text='BRAC end', xy=(pd.to_datetime(f'{year}-09-01'),
                                     text_position))

    # format month on the x-axis
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    # add relevant labels and titles
    ax.legend(loc='best')
    ax.set_ylabel('Unemployment rate (%)')
    ax.set_xlabel('Date')
    ax.set_title('Average Unemp Rate by BRAC Direct Changes Over Time,' +
                 f' {year}')

    # save and show graph
    hw3q1_plot = os.path.join(IMAGEPATH, "plot1.png")
    fig.savefig(hw3q1_plot)
    plt.show()


# plot three lines for unemployment rates
plot_gains_losses(merged_file, 2005)


# %% Section 2 Choropleth

# %%% Sub-Section 2a spatial mapping to show the direct affects of BRAC in US

def read_shp_file(folder, shp_file):
    """Read shp file."""
    shp = os.path.join(PATH, folder, shp_file)
    shp = geopandas.read_file(shp)
    return shp


def split_continental_and_territory_msas(state, msa):
    """Get the continental msas and territory msas for plotting."""
    state['GEOID'] = state['GEOID'].astype(int)
    # seperate remaining and extra states
    state_conti = state[(state['GEOID'] < 60) & (~state['STUSPS']
                                                 .isin(['HI', 'AK']))]
    state_terri = state[(state['GEOID'] > 60) | (state['STUSPS']
                                                 .isin(['HI', 'AK']))]
    # get territory msa data
    msa_terri = state_terri.sjoin(msa, how='inner', predicate='intersects')
    msa_terri.reset_index(drop=True, inplace=True)
    msa_terri = msa_terri.merge(msa, on='CBSAFP', how='left')
    msa_terri['geometry'] = msa_terri['geometry_y']
    # get continental msa data
    msa_terri_set = set(msa_terri['NAME_right'])
    msa_conti = msa.loc[~msa['NAME'].isin(msa_terri_set)]
    return state_conti, state_terri, msa_conti, msa_terri


# old fips to new fips mapping
old_new = {19380: 19660,  # Dayton OH
           70750: 12700,  # Bangor, ME
           70900: 12940,  # Barnstable, MA
           71650: 12700,  # Boston, MA
           71950: 14860,  # Bridgeport, CT
           72400: 15540,  # Burlington, VT
           73450: 25860,  # Hartford, CT
           75700: 35380,  # New Haven, CT
           76450: 35980,  # Norwich, CT
           76750: 38860,  # Portland, ME
           77200: 39300,  # Providence, RI
           78100: 44140}  # Springfield, MA


# replace old fips codes with new ones
def modify_and_merge_fips_brac(msa_df, brac_df, replace_dic):
    """Modify fips code to merge msa and brac data."""
    brac_df['area fips code'] = brac_df['area fips code'].replace(replace_dic)
    brac_df['area fips code'] = brac_df['area fips code']\
        .astype(int).astype(str)
    msa_df['CBSAFP'] = msa_df['CBSAFP'].astype(str)
    merged_msa_brac_df = brac_df.merge(msa_df, left_on='area fips code',
                                       right_on='CBSAFP', how='inner')
    return merged_msa_brac_df


def get_gdf(df):
    """Get the geo df based on geometry."""
    gdf = geopandas.GeoDataFrame(df, geometry=df['geometry'])
    return gdf


def plot_continentalUS(gdf, edge, column_to_plot):
    """Create spatial mapping to show the direct affects of BRAC in the US."""
    fig, ax = plt.subplots(figsize=(9, 6))
    # define divider, cax
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.1)
    # plot edge and direct data
    ax = edge.plot(ax=ax, color='white', edgecolor='black', legend=False)
    ax = gdf.plot(ax=ax, column='direct', cmap='coolwarm', edgecolor='gray',
                  legend=True, cax=cax)
    ax.set_title('Non-zero Direct Effects of BRAC, by Continental USA MSA')
    ax.axis('off');

    # save as png to local
    hw3q2_plot = os.path.join(IMAGEPATH, "plot2.png")
    fig.savefig(hw3q2_plot)


# Running functions for Q2
# load and read shp files
msa_shp = read_shp_file('tl_2019_us_cbsa', 'tl_2019_us_cbsa.shp')
state_shp = read_shp_file('cb_2018_us_state_5m', 'cb_2018_us_state_5m.shp')

# split the continental and territory states and msas, also for the extra
# credit question later
state_conti, state_terri, msa_conti,\
    msa_terri = split_continental_and_territory_msas(state_shp, msa_shp)

# get merged msa brac dataframe
merged_msa_brac_conti = modify_and_merge_fips_brac(msa_conti, brac_new,
                                                   old_new)
# get geometry points for continental US msas
gdf_state_conti = get_gdf(state_conti)
gdf_msa_conti = get_gdf(merged_msa_brac_conti)
# plot the state edge and msa dots colored based on the value of direct
plot_continentalUS(gdf_msa_conti, gdf_state_conti, 'direct')


# %%% Sub-Section Extra credit question

def get_single_state_msadata(state_list, state_df, gdf_msa_df):
    """Take a list of states to produce single state edge and msa brac data."""
    result = ()

    for state in state_list:
        state_edge = state_df[state_df['STUSPS'] == state]
        state_msa = gdf_msa_df[gdf_msa_df['STUSPS'] == state]
        # geo_state = get_gdf(state_edge)
        # geo_msa = get_gdf(state_msa)
        result += (state_edge, state_msa)
    return result


# create figure with one large continental subplot at the top and three
# territory state smaller subplots at the bottom
def plot_all_continents_territories():
    """Create a brac plot consisting of subplots for the entire US."""
    fig, axs = plt.subplots(3, 3, figsize=(12, 9))  # 3x3 subplots
    plt.subplots_adjust(wspace=0.01, hspace=0.1)
    # combine top 2*3 subplots into one big subplot for continental US
    gs = axs[0, 0].get_gridspec()
    for ax in axs[:2, :].ravel():
        ax.remove()
    ax1 = fig.add_subplot(gs[:2, :])

    # define subplots for non-continental states
    ax2 = plt.subplot(gs[2, 0])  # subplot for AK
    ax3 = plt.subplot(gs[2, 1])  # subplot for HI
    ax4 = plt.subplot(gs[2, 2])  # subplot for PR

    # define divider, cax, shared brac max, min for all subplots to be on the
    # same brac value scale
    divider = make_axes_locatable(ax1)
    cax = divider.append_axes('right', size='5%', pad=0.1)
    vmin = min(brac_new['direct'])
    vmax = max(brac_new['direct'])

    # adjust for alaska and hawaii's x, y axis
    ax2.set_xlim(-178, -125)
    ax2.set_ylim(46, 73)
    ax3.set_xlim(-164, -152)
    ax3.set_ylim(18, 23)

    # plot edge for each subplot
    ax1 = gdf_state_conti.plot(ax=ax1, color='white', edgecolor='black')
    ax2 = ak_edge.plot(ax=ax2, color='white', edgecolor='black')
    ax3 = hi_edge.plot(ax=ax3, color='white', edgecolor='black')
    ax4 = pr_edge.plot(ax=ax4, color='white', edgecolor='black')

    # plot brac data to each subplot, with black dot edge added
    ax1 = gdf_msa_conti.plot(ax=ax1, column='direct', edgecolor='gray',
                             legend=True, cmap='coolwarm',
                             vmin=vmin, vmax=vmax, cax=cax)
    ax2 = ak_msa.plot(ax=ax2, column='direct', edgecolor='gray', legend=True,
                      cmap='coolwarm', vmin=vmin, vmax=vmax, cax=cax)
    ax3 = hi_msa.plot(ax=ax3, column='direct', edgecolor='gray', legend=True,
                      cmap='coolwarm', vmin=vmin, vmax=vmax, cax=cax)
    ax4 = pr_msa.plot(ax=ax4, column='direct', edgecolor='gray', legend=True,
                      cmap='coolwarm', vmin=vmin, vmax=vmax, cax=cax)

    # remove axis for each subplot
    for ax in [ax1, ax2, ax3, ax4]:
        ax.axis('off')
        # remove the axis ticks
        ax.set_xticks([])
        ax.set_yticks([])
        # remove the axis spines
        for spine in ax.spines.values():
            spine.set_visible(False)

    # create one legend on the first plot
    sm = plt.cm.ScalarMappable(cmap='coolwarm', norm=plt.Normalize(vmin=vmin,
                                                                   vmax=vmax))
    sm._A = []
    fig.colorbar(sm, cax=cax)

    # set plot title
    ax1.set_title('Non-zero Direct Effects of BRAC ' +
                  'by Continental and Territory US MSA')
    ax2.set_title('AK (size adjusted)')
    ax3.set_title('HI (size adjusted)')
    ax4.set_title('PR');

    # save as png to local
    hw3q2extracredit_plot = os.path.join(IMAGEPATH, "plot3_allstates.png")
    fig.savefig(hw3q2extracredit_plot)


# get only modified state and msa brac data for territory states
merged_msa_brac_terri = modify_and_merge_fips_brac(msa_terri, brac_new,
                                                   old_new)
gdf_state_terri = get_gdf(state_terri)
gdf_msa_terri = get_gdf(merged_msa_brac_terri)

# create seperate state and msa brac data for AK, HI, and PR
ak_edge, ak_msa, hi_edge, hi_msa, pr_edge,\
    pr_msa = get_single_state_msadata(['AK', 'HI', 'PR'], gdf_state_terri,
                                      gdf_msa_terri)

# plot the data for all continents and territories
plot_all_continents_territories()
