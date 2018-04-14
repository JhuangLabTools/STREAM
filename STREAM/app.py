### CRISPR-SURF Dash Application
import dash
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from upload_button import FilesUpload, upload_files
from flask import Flask, request, redirect, url_for, render_template, jsonify, send_from_directory, send_file, session
import requests
import re
import subprocess as sb
import numpy as np
import pandas as pd
import sys
import os
import glob
import base64
import urllib
import ast
import random
import gzip
import uuid
import json
import cPickle as cp
import csv

# STREAM logo
stream_logo = 'stream_logo.png'
stream_logo_image = base64.b64encode(open(stream_logo, 'rb').read())

mgh_logo = 'mgh.png'
mgh_logo_image = base64.b64encode(open(mgh_logo, 'rb').read())

mitbe_logo = 'mitbe.png'
mitbe_logo_image = base64.b64encode(open(mitbe_logo, 'rb').read())

hms_logo = 'hms.png'
hms_logo_image = base64.b64encode(open(hms_logo, 'rb').read())

# Generate ID to initialize CRISPR-SURF instance
server = Flask(__name__)
server.secret_key = '~x94`zW\sfa24\xa2qdx20g\x9dl\xc0x35x90\kchs\x9c\xceb\xb4'
app = dash.Dash(name = 'stream-app', server = server, url_base_pathname = '/compute/', csrf_protect=False)
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

app2 = dash.Dash(name = 'stream-app-precomputed', server = server, url_base_pathname = '/precomputed/', csrf_protect=False)
app2.css.config.serve_locally = True
app2.scripts.config.serve_locally = True

dcc._css_dist[0]['relative_package_path'].append('STREAM.css')
dcc._css_dist[0]['relative_package_path'].append('Loading-State.css')

app.server.config['UPLOADS_FOLDER']='/tmp/UPLOADS_FOLDER'
app.server.config['RESULTS_FOLDER']='/tmp/RESULTS_FOLDER'


@server.route('/help')
def help():
	return render_template('help.html')

@server.route('/')
def index():
	newpath = 'STREAM_' + str(uuid.uuid4())

	UPLOADS_FOLDER = os.path.join(app.server.config['UPLOADS_FOLDER'], newpath)
	RESULTS_FOLDER = os.path.join(app.server.config['RESULTS_FOLDER'], newpath)

	if not os.path.exists(UPLOADS_FOLDER):
		os.makedirs(UPLOADS_FOLDER)

	if not os.path.exists(RESULTS_FOLDER):
		os.makedirs(RESULTS_FOLDER)

	param_dict = {'compute-clicks':0, 'sg-clicks':0, 'discovery-clicks':0, 'correlation-clicks':0, 'starting-nodes':['S0'],
	'sg-genes':['False'], 'discovery-genes':['False'], 'correlation-genes':['False'], 'sg-gene':'False', 'discovery-gene':'False', 'correlation-gene':'False',
	'compute-run':False,'sg-run':False,'discovery-run':False, 'correlation-run':False, 'required_files': ['Gene Expression Matrix', 'Cell Labels', 'Cell Label Colors'],
	'checkbutton1':1, 'checkpoint1':True,'checkbutton2':1, 'checkpoint2':True,'checkbutton3':1, 'checkpoint3':True,'checkbutton4':1, 'checkpoint4':True}

	with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
		json_string = json.dumps(param_dict)
		f.write(json_string + '\n')


	return render_template('index.html',newpath=newpath)
	#return redirect('/compute/' + newpath)

#Import some other useful functions
def generate_table(dataframe, max_rows = 100):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

# Upload file

upload_url1='/uploadajax1'

@app.server.route(upload_url1, methods = ['POST'])
def save_files1():

	folder_location = request.referrer
	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(folder_location.split('/')[-1])

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	rem_files = []
	for i in param_dict['required_files']:
		rem_file = glob.glob(UPLOADS_FOLDER + '/' + '_'.join(map(str, i.split())) + '*')
		try:
			rem_files.append(rem_file[0])
		except:
			continue

	for i in rem_files:
		sb.call('rm %s' % i, shell = True)

	return upload_files(param_dict['required_files'], UPLOADS_FOLDER)

app2.layout = html.Div([

	html.Img(src='data:image/png;base64,{}'.format(stream_logo_image), width = '50%'),
	html.H2('Single-cell Trajectory Reconstruction Exploration And Mapping'),

	html.Br(),
	html.Hr(),

	html.H3('Choose Pre-Computed Data Set'),

	dcc.Dropdown(
		id = 'precomp-dataset',
	    options=[
	        {'label': 'Nestorowa et al. (2016)', 'value': 'Nestorowa_et_al'},
	    ],
	    value = 'Nestorowa_et_al'
	),

	html.Br(),
	html.Hr(),

	html.H3('Visualize Trajectories'),

	html.Button(id = 'graph-button2', children = '(+) Show', n_clicks = 0),

	html.Label('Select Starting Branch', style = {'font-weight':'bold', 'padding-right':'10px'}),
	dcc.Dropdown(
			id = 'root2',
		    options=[
		        {'label': 'S0', 'value': 'S0'},
		    ],
		    value='S0'
		),

	html.Div(

		id = 'graph-container2',
		children = [

		html.Div(

			id = '3d-scatter-container',
			children = [

				html.H3('3D Scatter Plot'),
				dcc.Graph(id='3d-scatter2', animate=False),

				html.H3('Flat Tree Plot'),
				dcc.Graph(id='flat-tree-scatter2', animate=False),

			], className = 'six columns'),

		html.Div(

			id = '2d-subway-container',
			children = [

				html.H3('2D Subway Map'),
				dcc.Graph(id='2d-subway2', animate=False),

				html.H3('Stream Plot'),
				html.Img(id = 'rainbow-plot2', src = None, width = '70%', style = {'align':'middle'}),

			], className = 'six columns'),

		], className = 'row'),

	html.Br(),
	html.Hr(),

	html.H3('Visualize Genes of Interest'),

	html.Button(id = 'sg-plot-button2', children = '(+) Show', n_clicks = 0),

	html.Div(

		id = 'sg-plot-container2',
		children = [

		html.Div([

			html.Br(),

			html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
			dcc.Dropdown(
					id = 'sg-gene2',
				    options=[
				        {'label': 'Choose gene!', 'value': 'False'}
				    ],
				    value = 'False'
				),

			html.Br(),

			]),

		html.Div([

			html.Div([

				dcc.Graph(id='2d-subway-sg2', animate=False)

				], className = 'six columns'),


			html.Div([

				html.Img(id = 'sg-plot2', src = None, width = '100%', style = {'align':'middle'}),

				], className = 'six columns'),

			], className = 'row'),

		]),

	html.Br(),
	html.Hr(),

	html.H3('Visualize Diverging Genes'),

	html.Button(id = 'discovery-plot-button2', children = '(+) Show', n_clicks = 0),

	html.Div(
		id = 'discovery-container2',
		children = [

		html.Br(),

		html.Div(

			id = 'discovery-plot-container2',
			children = [

			html.Div([

				html.Label('Branches for Diverging Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Dropdown(
						id = 'de-branches2',
					    options=[
					        {'label': 'Choose branch!', 'value': 'False'}
					    ],
					    value = 'False'
					),

		        html.Br(),

		        html.Label('Relatively Highly Expressed On:', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.RadioItems(
			    	id = 'de-direction2',
			        options=[
			            {'label': 'Choose branch pair above', 'value': 'False'}
			        ]),

		        html.Br(),

				html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Slider(
			        id='de-slider2',
			        min=0,
			        max=50,
			        value=10,
			        step=1
		        ),

		        html.Br(),

				html.Div(id = 'discovery-table2', style = {'font-family': 'courier', 'align':'center'}),

				], className = 'five columns'),


			html.Div([

				html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
				dcc.Dropdown(
						id = 'discovery-gene2',
					    options=[
					        {'label': 'Choose gene!', 'value': 'False'}
					    ],
					    value = 'False'
					),

				dcc.Graph(id='2d-subway-discovery2', animate=False),

				html.Img(id = 'discovery-plot2', src = None, width = '70%', style = {'align':'middle'}),

				], className = 'seven columns'),

			], className = 'row'),

		]),

	html.Br(),
	html.Hr(),

	html.H3('Visualize Transition Genes'),

	html.Button(id = 'correlation-plot-button2', children = '(+) Show', n_clicks = 0),

	html.Div(
		id = 'correlation-container2',
		children = [

		html.Br(),

		html.Div(

			id = 'correlation-plot-container2',
			children = [

			html.Div([

				html.Label('Branch for Transition Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Dropdown(
						id = 'corr-branches2',
					    options=[
					        {'label': 'Choose branch!', 'value': 'False'}
					    ],
					    value = 'False'
					),

		        html.Br(),

				html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
		        dcc.Slider(
			        id='corr-slider2',
			        min=0,
			        max=50,
			        value=10,
			        step=1
		        ),

		        html.Br(),

				html.Div(id = 'correlation-table2', style = {'font-family': 'courier', 'align':'center'}),

				], className = 'five columns'),


			html.Div([

				html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
				dcc.Dropdown(
						id = 'correlation-gene2',
					    options=[
					        {'label': 'Choose gene!', 'value': 'False'}
					    ],
					    value = 'False'
					),

				dcc.Graph(id='2d-subway-correlation2', animate=False),

				html.Img(id = 'correlation-plot2', src = None, width = '70%', style = {'align':'middle'}),

				], className = 'seven columns'),

			], className = 'row'),

		])

	])

app.layout = html.Div([

	dcc.Location(id='url', refresh=False),

	dcc.Interval(id='common-interval', interval=2000),

	dcc.Interval(id='common-interval-1', interval=1000000),
	dcc.Interval(id='common-interval-2', interval=1000000),
	dcc.Interval(id='common-interval-3', interval=1000000),
	dcc.Interval(id='common-interval-4', interval=1000000),

	html.Div(id = 'custom-loading-states-1',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Div(id = 'custom-loading-states-2',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Div(id = 'custom-loading-states-3',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Div(id = 'custom-loading-states-4',
		children = [

		html.Div(id = 'custom-loading-state1', className = '_dash-loading-callback_custom', children = ['Loading...', html.Center(children=[html.Div(id = 'custom-loading-state2', className = 'loader', style = {'display':'block'})])],  style = {'display':'block'})

		], style = {'display':'none'}),

	html.Img(src='data:image/png;base64,{}'.format(stream_logo_image), width = '50%'),
	html.H2('Single-cell Trajectory Reconstruction Exploration And Mapping'),

	html.Hr(),

	html.Div([

		html.Div([

			html.H3(id = 'buffer1', children = 'Step 1: Input Files'),

			], className = 'six columns'),

		# html.Div([

		# 	html.H3(id = 'buffer2', children ='Basic Parameters'),

		# 	], className = 'six columns'),

		], className = 'row'),

	html.Div([

		# Input files
		html.Div([

			html.H3(id = 'buffer5', children = 'Personal Files'),

			FilesUpload(
				        id='required-files',
				        label = 'tmp',
				        uploadUrl=upload_url1,
					    ),

			html.Hr(),

			html.Label(id = 'matrix-upload', children = 'Gene Expression Matrix: None', style = {'font-weight':'bold'}),
			html.Label(id = 'cl-upload', children = 'Cell Labels File: None', style = {'font-weight':'bold'}),
			html.Label(id = 'clc-upload', children = 'Cell Label Colors File: None', style = {'font-weight':'bold'}),

			html.Hr(),

			html.H3(id = 'buffer5', children = 'Example Files'),

			html.Button(id = 'load_example_data', children = 'Load Example Data', n_clicks = 0),

			], className = 'six columns', style = {'border-style':'solid','border-width':'2px', 'border-color':'#DCDCDC','border-radius':'10px','border-spacing':'15px','padding':'10px'}),

		# Input Parameters
		html.Div([

			html.H3(id = 'buffer2', children ='Basic Parameters'),

			html.Div([

				html.Div([

					html.Label('Perform Log2 Transformation', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'log2',
				        options=[
				            {'label': 'Yes', 'value': 'True'},
				            {'label': 'No', 'value': 'False'}
				        ],
				        value = 'False',
				        labelStyle={'display': 'inline-block'}),

					html.Label('Normalize Data on Library Size', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'norm',
				        options=[
				            {'label': 'Yes', 'value': 'True'},
				            {'label': 'No', 'value': 'False'}
				        ],
				        value = 'False',
				        labelStyle={'display': 'inline-block'}),

					html.Label('ATAC-seq Data', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'atac',
				        options=[
				            {'label': 'Yes', 'value': 'True'},
				            {'label': 'No', 'value': 'False'}
				        ],
				        value = 'False',
				        labelStyle={'display': 'inline-block'}),

					html.Label('Variable Gene Selection', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.RadioItems(
				    	id = 'select',
				        options=[
				            {'label': 'LOESS', 'value': 'LOESS'},
				            {'label': 'PCA', 'value': 'PCA'},
				            {'label': 'None', 'value': 'all'}
				        ],
				        value = 'LOESS',
				        labelStyle={'display': 'inline-block'}),

					], className = 'six columns'),


				html.Div([

					html.Label('LLE Neighbours', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Input(id = 'lle-nbs', value = 0.1),

					html.Label('LLE Dimension Reduction', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Input(id = 'lle-dr', value = 3),

					], className = 'six columns'),

				], className = 'row'),

				html.Div([

					html.H3('Advanced Parameters'),

					html.Button(children = '(+) Show', id = 'advanced-params-button', n_clicks = 0, style = {'margin-bottom':'0.5cm'}),

					html.Div(id = 'advanced-params-container', children = [

						html.Div([

							html.Div([

								html.Label('LOESS Fraction', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'loess_frac', value = 0.1),

								html.Label('Number of PCs', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'pca_n_PC', value = 15),

								html.Label('Keep First PC', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'pca_first_PC',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								html.Label('Feature Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'feature_genes', value = None),

								html.Label('AP Damping Factor', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'AP_damping_factor', value = 0.75),

								], className = 'three columns'),

							html.Div([

								html.Label('EPG Nodes', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_n_nodes', value = 50),

								html.Label('EPG Lambda', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_lambda', value = 0.02),

								html.Label('EPG Mu', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_mu', value = 0.1),

								html.Label('EPG Trimming Radius', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_trimmingradius', value = 1000000),

								html.Label('EPG Final Energy', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_finalenergy',
							        options=[
								        {'label': 'Penalized', 'value': 'Penalized'},
							            {'label': 'Base', 'value': 'Base'},
							        ],
							        value = 'Penalized'),

								html.Label('EPG Alpha', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_alpha', value = 0.02),

								html.Label('EPG Beta', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_beta', value = 0),


								], className = 'three columns'),

							html.Div([

								html.Label('Disable EPG Collapse', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'disable_EPG_collapse',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								html.Label('EPG Collapse Mode', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_collapse_mode',
							        options=[
								        {'label': 'Point Number', 'value': 'PointNumber'},
							            {'label': 'Point Number Extrema', 'value': 'PointNumber_Extrema'},
							            {'label': 'Point Number Leaves', 'value': 'PointNumber_Leaves'},
							            {'label': 'Edges Number', 'value': 'EdgesNumber'},
							            {'label': 'Edges Length', 'value': 'EdgesLength'},
							        ],
							        value = 'PointNumber'),

								html.Label('EPG Collapse Parameter', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_collapse_par',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								], className = 'three columns'),

							html.Div([

								html.Label('EPG Shift', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_shift',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								html.Label('EPG Shift Mode', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_shift_mode',
							        options=[
								        {'label': 'Node Density', 'value': 'NodeDensity'},
							            {'label': 'Node Points', 'value': 'NodePoints'},
							        ],
							        value = 'NodeDensity'),

								html.Label('EPG Shift DR', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_shift_DR', value = 0.05),

								html.Label('EPG Max Shift', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_shift_maxshift', value = 5),

								html.Label('Disable EPG Extend', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'disable_EPG_ext',
							        options=[
							            {'label': 'Yes', 'value': 'True'},
							            {'label': 'No', 'value': 'False'}
							        ],
							        value = 'False',
							        labelStyle={'display': 'inline-block'}),

								html.Label('EPG Extend Mode', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.RadioItems(
							    	id = 'EPG_ext_mode',
							        options=[
								        {'label': 'Quant Dists', 'value': 'QuantDists'},
							            {'label': 'Quant Centroid', 'value': 'QuantCentroid'},
							            {'label': 'Weighted Centroid', 'value': 'WeightedCentroid'},
							        ],
							        value = 'QuantDists'),

								html.Label('EPG Extend Parameter', style = {'font-weight':'bold', 'padding-right':'10px'}),
								dcc.Input(id = 'EPG_ext_par', value = 0.5),

								], className = 'three columns'),

							], className = 'row')

						]),

					]),

			], className = 'six columns', style = {'border-style':'solid','border-width':'2px', 'border-color':'#DCDCDC','border-radius':'10px','border-spacing':'15px','padding':'10px'})

		], className = 'row'),

	html.Hr(),

	html.H3(id = 'buffer3', children = 'Step 2: Compute Trajectories'),

	html.Button('Compute', id='compute-button'),

	html.Br(),
	html.Br(),
	html.Br(),

	html.Div(id = 'compute-container',
		children = [

		html.Div([

			html.Div([

				html.Label('Select Starting Branch', style = {'font-weight':'bold', 'padding-right':'10px'}),
				dcc.Dropdown(
						id = 'root',
					    options=[
					        {'label': 'S0', 'value': 'S0'},
					    ],
					    value='S0'
					),

				]),

			]),

		html.Br(),
		html.Br(),

		html.Button(id = 'graph-button', children = '(-) Hide Graphs', n_clicks = 0),

		html.Div(

			id = 'graph-container',
			children = [

			html.Div(

				id = '3d-scatter-container',
				children = [

					html.H3('3D Scatter Plot'),
					dcc.Graph(id='3d-scatter', animate=False),

					html.H3('Flat Tree Plot'),
					dcc.Graph(id='flat-tree-scatter', animate=False),

				], className = 'six columns'),

			html.Div(

				id = '2d-subway-container',
				children = [

					html.H3('2D Subway Map'),
					dcc.Graph(id='2d-subway', animate=False),

					html.H3('Stream Plot'),
					html.Img(id = 'rainbow-plot', src = None, width = '70%', style = {'align':'middle'}),



				], className = 'six columns'),

			], className = 'row'),

		html.Br(),
		html.Br(),

		]),

	html.Hr(),

	html.Div([

		html.H3('Step 3A: Visualize Genes of Interest'),
		html.Button(id = 'sg-button', children = 'Get Started!', n_clicks = 0),

		html.Br(),
		html.Br(),
		html.Br(),

		html.Div(
			id = 'sg-container',
			children = [

			html.Button(id = 'sg-plot-button', children = '(-) Hide Graphs', n_clicks = 0),

			html.Br(),
			html.Br(),

			html.Div(

				id = 'sg-plot-container',
				children = [

				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'sg-gene',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					html.Br(),
					html.Br(),

					html.Button(id = 'sg-compute', children = 'Visualize Gene', n_clicks = 0),

					]),

				html.Div([

					html.Div([

						dcc.Graph(id='2d-subway-sg', animate=False)

						], className = 'six columns'),


					html.Div([

						html.Img(id = 'sg-plot', src = None, width = '100%', style = {'align':'middle'}),

						], className = 'six columns'),

					], className = 'row'),

				]),

			])

		]),

	html.Hr(),

	html.Div([

		html.H3(id = 'buffer4', children = 'Step 3B: Identify Diverging Genes'),
		html.Button(id = 'discovery-button', children = 'Compute', n_clicks = 0),

		html.Br(),
		html.Br(),
		html.Br(),

		html.Div(
			id = 'discovery-container',
			children = [

			html.Button(id = 'discovery-plot-button', children = '(-) Hide Graphs', n_clicks = 0),

			html.Br(),
			html.Br(),

			html.Div(

				id = 'discovery-plot-container',
				children = [

				html.Div([

					html.Label('Branches for Diverging Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Dropdown(
							id = 'de-branches',
						    options=[
						        {'label': 'Choose branch!', 'value': 'False'}
						    ],
						    value = 'False'
						),

			        html.Br(),

			        html.Label('Relatively Highly Expressed On:', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.RadioItems(
				    	id = 'de-direction',
				        options=[
				            {'label': 'Choose branch pair above', 'value': 'False'}
				        ]),

			        html.Br(),

					html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Slider(
				        id='de-slider',
				        min=0,
				        max=50,
				        value=10,
				        step=1
			        ),

			        html.Br(),

					html.Div(id = 'discovery-table', style = {'font-family': 'courier', 'align':'center'}),

					], className = 'five columns'),


				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'discovery-gene',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					dcc.Graph(id='2d-subway-discovery', animate=False),

					html.Img(id = 'discovery-plot', src = None, width = '70%', style = {'align':'middle'}),

					], className = 'seven columns'),

				], className = 'row'),

			])

		]),

	html.Hr(),

	html.Div([

		html.H3(id = 'buffer5', children = 'Step 3C: Identify Transition Genes'),
		html.Button(id = 'correlation-button', children = 'Compute', n_clicks = 0),

		html.Br(),
		html.Br(),
		html.Br(),

		html.Div(
			id = 'correlation-container',
			children = [

			html.Button(id = 'correlation-plot-button', children = '(-) Hide Graphs', n_clicks = 0),

			html.Br(),
			html.Br(),

			html.Div(

				id = 'correlation-plot-container',
				children = [

				html.Div([

					html.Label('Branch for Transition Gene Analysis', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Dropdown(
							id = 'corr-branches',
						    options=[
						        {'label': 'Choose branch!', 'value': 'False'}
						    ],
						    value = 'False'
						),

			        html.Br(),

					html.Label('Number of Genes', style = {'font-weight':'bold', 'padding-right':'10px'}),
			        dcc.Slider(
				        id='corr-slider',
				        min=0,
				        max=50,
				        value=10,
				        step=1
			        ),

			        html.Br(),

					html.Div(id = 'correlation-table', style = {'font-family': 'courier', 'align':'center'}),

					], className = 'five columns'),


				html.Div([

					html.Label('Gene', style = {'font-weight':'bold', 'padding-right':'10px'}),
					dcc.Dropdown(
							id = 'correlation-gene',
						    options=[
						        {'label': 'Choose gene!', 'value': 'False'}
						    ],
						    value = 'False'
						),

					dcc.Graph(id='2d-subway-correlation', animate=False),

					html.Img(id = 'correlation-plot', src = None, width = '70%', style = {'align':'middle'}),

					], className = 'seven columns'),

				], className = 'row'),

			])

		]),

	html.Hr(),

	html.Div([

		html.Div([

			html.Img(src='data:image/png;base64,{}'.format(hms_logo_image), width = '25%'),

			], className = 'four columns'),

		html.Div([

			html.Img(src='data:image/png;base64,{}'.format(mitbe_logo_image), width = '40%'),

			html.H3([html.Center([html.A('Pinello Lab', href='http://www.pinellolab.org/')])]),

			html.Label('Credits: H Chen, L Albergante, JY Hsu, CA Lareau, GL Bosco, J Guan, S Zhou, AN Gorban, DE Bauer, MJ Aryee, DM Langenau, A Zinovyev, JD Buenrostro, GC Yuan, L Pinello', style = {'font-weight':'bold'})

			], className = 'four columns'),

		html.Div([

			html.Img(src='data:image/png;base64,{}'.format(mgh_logo_image), width = '26%'),

			], className = 'four columns'),
		], className = 'row', style = {'text-align':'center'})

	])

#### INPUT FILES ######
@app.callback(
    Output('required-files', 'label'),
    [Input('url', 'pathname')])

def update_input_files(pathname):

	file_names = ['Gene Expression Matrix', 'Cell Labels', 'Cell Label Colors']

	return ','.join(file_names)

#### Load exmample data
@app.callback(
    Output('select', 'value'),
    [Input('url', 'pathname'),
    Input('load_example_data', 'n_clicks'),
    Input('atac', 'value')])

def update_select_features(pathname, n_clicks, atac):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if n_clicks > 0:

			return 'all'

		elif str(atac) == 'True':

			return 'PCA'

		else:

			return 'LOESS'

	else:

		return 'LOESS'

@app.callback(
    Output('load_example_data', 'children'),
    [Input('url', 'pathname'),
    Input('load_example_data', 'n_clicks')])

def update_input_files(pathname, n_clicks):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if n_clicks > 0:

			sb.call('cp /STREAM/exampleDataset/data_guoji.tsv %s/Gene_Expression_Matrix_data_guoji.tsv' % (UPLOADS_FOLDER), shell = True)
			sb.call('cp /STREAM/exampleDataset/cell_label.tsv %s/Cell_Labels_cell_label.tsv' % (UPLOADS_FOLDER), shell = True)
			sb.call('cp /STREAM/exampleDataset/cell_label_color.tsv %s/Cell_Label_Colors_cell_label_color.tsv' % (UPLOADS_FOLDER), shell = True)

			return 'Example Data Loaded!'

		else:

			return 'Load Example Data'

	else:

		return 'Load Example Data'

# Advanced parameters
@app.callback(
	Output('advanced-params-button', 'children'),
	[Input('advanced-params-button', 'n_clicks')])

def update_advanced_params_button(n_clicks):

	if n_clicks%2 == 0:
		return '(+) Show'
	else:
		return '(-) Hide'

@app.callback(
	Output('advanced-params-container', 'style'),
	[Input('advanced-params-button', 'n_clicks')])

def update_advanced_params_container(n_clicks):

	if n_clicks%2 == 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

################################# COMPUTE TRAJECTORIES #################################
@app.callback(
    Output('compute-container', 'style'),
    [Input('3d-scatter', 'figure'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-clicks'] > 0:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
	Output('matrix-upload', 'children'),
	[Input('url', 'pathname')],
	events=[Event('common-interval', 'interval')])

def update_matrix_log(pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
		cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
		cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

		if len(matrix) > 0:

			if matrix[0].endswith('tsv'):

				df = pd.read_table(matrix[0], sep = '\t', header = None)
				if str(df.get_value(0,0)) == 'nan':

					df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

				else:
					return 'Gene Expression Matrix: [ERROR] Column and row IDs must be present ...'

			elif matrix[0].endswith('txt'):

				df = pd.read_table(matrix[0], sep = '\t', header = None)
				if str(df.get_value(0,0)) == 'nan':

					df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

				else:
					return 'Gene Expression Matrix: [ERROR] Column and row IDs must be present ...'

			elif matrix[0].endswith('csv'):

				df = pd.read_table(matrix[0], sep = ',', header = None)
				if str(df.get_value(0,0)) == 'nan':

					df = pd.read_table(matrix[0], index_col = 0, sep = ',')

				else:
					return 'Gene Expression Matrix: [ERROR] Column and row IDs must be present ...'

			else:
				return 'Gene Expression Matrix: [ERROR] File format needs to be .tsv, .csv, or .txt ...'

			if len(df.columns) > 1000:
					return 'Gene Expression Matrix: [ERROR] Limit of 1000 cells (Detected %s Cells) ...' % len(df.columns)

			elif df.isnull().values.any():
				return 'Gene Expression Matrix: [ERROR] NaN values detected in matrix ...'

			elif df._get_numeric_data().size != df.size:
				return 'Gene Expression Matrix: [ERROR] Matrix contains non-numeric values ...'

			else:
				return 'Gene Expression Matrix: Upload successful!'

		else:
			return 'Gene Expression Matrix: No upload'

@app.callback(
	Output('cl-upload', 'children'),
	[Input('url', 'pathname')],
	events=[Event('common-interval', 'interval')])

def update_cl_log(pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
		cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
		cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

		if len(matrix) > 0:

			if matrix[0].endswith('tsv'):

				df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

			elif matrix[0].endswith('txt'):

				df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

			elif matrix[0].endswith('csv'):

				df = pd.read_table(matrix[0], index_col = 0, sep = ',')

			if len(cell_label) > 0 and len(cell_label_colors) == 0:

				cl = pd.read_table(cell_label[0], header = None)
				if len(cl.columns) == 1 and cl.size == len(df.columns):
					return 'Cell Labels File: Upload successful!'

				else:
					return 'Cell Labels File: [ERROR] Cell Labels file contains incorrect number of labels (%s Labels for %s Cells)' % (cl.size, len(df.columns))

			elif len(cell_label) > 0 and len(cell_label_colors) > 0:

				try:
					cl = pd.read_table(cell_label[0], header = None)
					clc = pd.read_table(cell_label_colors[0], header = None)
					if len(cl.columns) == 1 and cl.size == len(df.columns):
						matches = []
						for i in clc.iloc[:,1].tolist():
							if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', i):
								matches.append(1)

						if list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])) and sum(matches) == len(clc.iloc[:,1].tolist()):
							return 'Cell Labels File: Upload successful!'

						elif list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])):
							return 'Cell Labels File: Upload successful!'

						else:
							return 'Cell Labels File: [ERROR] Disagreement between number of Cell Labels and Cell Label Colors ...'

					else:
						return 'Cell Labels File: [ERROR] Cell Labels file contains incorrect number of labels (%s Labels for %s Cells) ...' % (cl.size, len(df.columns))

				except:
					return 'Cell Labels File: [ERROR] Disagreement between Cell Labels and Cell Label Colors files ...'

			return 'Cell Labels File: No upload'

		else:

			if len(cell_label) > 0:
				return 'Cell Labels File: Upload successful, but no input gene expression matrix ...'
			else:
				return 'Cell Labels File: No upload'

@app.callback(
	Output('clc-upload', 'children'),
	[Input('url', 'pathname')],
	events=[Event('common-interval', 'interval')])

def update_clc_log(pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
		cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
		cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

		if len(matrix) > 0:

			if matrix[0].endswith('tsv'):

				df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

			elif matrix[0].endswith('txt'):

				df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

			elif matrix[0].endswith('csv'):

				df = pd.read_table(matrix[0], index_col = 0, sep = ',')

			if len(cell_label) == 0 and len(cell_label_colors) > 0:
				return 'Cell Label Colors File: [ERROR] Needs to be accompanied with a Cell Labels file'

			elif len(cell_label) > 0 and len(cell_label_colors) > 0:

				try:
					cl = pd.read_table(cell_label[0], header = None)
					clc = pd.read_table(cell_label_colors[0], header = None)
					if len(cl.columns) == 1 and cl.size == len(df.columns):
						matches = []
						for i in clc.iloc[:,1].tolist():
							if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', i):
								matches.append(1)

						if list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])) and sum(matches) == len(clc.iloc[:,1].tolist()):
							return 'Cell Label Colors File: Upload successful!'

						elif list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])):
							return 'Cell Label Colors File: [ERROR] Does not provide HEX color code ...'

						else:
							return 'Cell Label Colors File: [ERROR] Disagreement between number of Cell Labels and Cell Label Colors ...'

					else:
						return 'Cell Label Colors File: Upload successful!'

				except:
					return 'Cell Label Colors File: [ERROR] Disagreement between Cell Labels and Cell Label Colors files ...'

			return 'Cell Label Colors File: No upload'

		else:

			if len(cell_label) > 0 and len(cell_label_colors) > 0:
				return 'Cell Labels Colors File: Upload successful, but no input gene expression matrix ...'
			elif len(cell_label_colors) > 0:
				return 'Cell Labels Colors File: Upload successful, but no input gene expression matrix or cell labels file...'
			else:
				return 'Cell Label Colors File: No upload'

@app.callback(
    Output('compute-button', 'disabled'),
    [Input('compute-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
		cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
		cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

		if len(matrix) > 0:

			if n_clicks > param_dict['compute-clicks']:
				return True
			else:

				if matrix[0].endswith('tsv'):

					df = pd.read_table(matrix[0], sep = '\t', header = None)
					if str(df.get_value(0,0)) == 'nan':

						df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

					else:
						return True

				elif matrix[0].endswith('txt'):

					df = pd.read_table(matrix[0], sep = '\t', header = None)
					if str(df.get_value(0,0)) == 'nan':

						df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

					else:
						return True

				elif matrix[0].endswith('csv'):

					df = pd.read_table(matrix[0], sep = ',', header = None)
					if str(df.get_value(0,0)) == 'nan':

						df = pd.read_table(matrix[0], index_col = 0, sep = ',')

					else:
						return True

				else:
					return True

				if len(df.columns) > 1000:
						return True

				elif df.isnull().values.any():
					return True

				elif df._get_numeric_data().size != df.size:
					return True

				else:

					if len(cell_label) > 0 and len(cell_label_colors) == 0:

						cl = pd.read_table(cell_label[0], header = None)
						if len(cl.columns) == 1 and cl.size == len(df.columns):
							return False

						else:
							return True

					elif len(cell_label) > 0 and len(cell_label_colors) > 0:

						try:
							cl = pd.read_table(cell_label[0], header = None)
							clc = pd.read_table(cell_label_colors[0], header = None)
							if len(cl.columns) == 1 and cl.size == len(df.columns):
								matches = []
								for i in clc.iloc[:,1].tolist():
									if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', i):
										matches.append(1)

								if list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])) and sum(matches) == len(clc.iloc[:,1].tolist()):
									return False

								elif list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])):
									return True

								else:
									return True

							else:
								return True

						except:
							return True

					return False

		else:

			return True

	else:
		return True

@app.callback(
    Output('compute-button', 'children'),
    [Input('compute-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
		cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
		cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

		if len(matrix) > 0:

			if n_clicks > param_dict['compute-clicks']:
				return 'Running...'
			else:

				if matrix[0].endswith('tsv'):

					df = pd.read_table(matrix[0], sep = '\t', header = None)
					if str(df.get_value(0,0)) == 'nan':

						df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

					else:
						return 'ERROR: Column and row IDs must be present ...'

				elif matrix[0].endswith('txt'):

					df = pd.read_table(matrix[0], sep = '\t', header = None)
					if str(df.get_value(0,0)) == 'nan':

						df = pd.read_table(matrix[0], index_col = 0, sep = '\t')

					else:
						return 'ERROR: Column and row IDs must be present ...'

				elif matrix[0].endswith('csv'):

					df = pd.read_table(matrix[0], sep = ',', header = None)
					if str(df.get_value(0,0)) == 'nan':

						df = pd.read_table(matrix[0], index_col = 0, sep = ',')

					else:
						return 'ERROR: Column and row IDs must be present ...'

				else:
					return 'ERROR: File format needs to be .tsv, .csv, or .txt ...'

				if len(df.columns) > 1000:
						return 'ERROR: Limit of 1000 cells (Detected %s Cells) ...' % len(df.columns)

				elif df.isnull().values.any():
					return 'ERROR: NaN values detected in matrix ...'

				elif df._get_numeric_data().size != df.size:
					return 'ERROR: Matrix contains non-numeric values ...'

				else:

					if len(cell_label) > 0 and len(cell_label_colors) == 0:

						cl = pd.read_table(cell_label[0], header = None)
						if len(cl.columns) == 1 and cl.size == len(df.columns):
							return 'Compute'

						else:
							return 'ERROR: Cell Labels file contains incorrect number of labels (%s Labels for %s Cells)' % (cl.size, len(df.columns))

					elif len(cell_label) > 0 and len(cell_label_colors) > 0:

						try:
							cl = pd.read_table(cell_label[0], header = None)
							clc = pd.read_table(cell_label_colors[0], header = None)
							if len(cl.columns) == 1 and cl.size == len(df.columns):
								matches = []
								for i in clc.iloc[:,1].tolist():
									if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', i):
										matches.append(1)

								if list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])) and sum(matches) == len(clc.iloc[:,1].tolist()):
									return 'Compute'

								elif list(set(clc.iloc[:,0])) == list(set(cl.iloc[:,0])):
									return 'ERROR: Cell Label Colors file does not provide HEX color code ...'

								else:
									return 'ERROR: Disagreement between number of Cell Labels and Cell Label Colors ...'

							else:
								return 'ERROR: Cell Labels file contains incorrect number of labels (%s Labels for %s Cells)' % (cl.size, len(df.columns))

						except:
							return 'ERROR: Disagreement between Cell Labels and Cell Label Colors files ...'

					return 'Compute'

		else:
			return 'Load Personal or Example Data (Step 1)'

	else:
		return 'Load Personal or Example Data (Step 1)'

@app.callback(
	Output('graph-button', 'children'),
	[Input('graph-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graphs'
	else:
		return '(-) Hide Graphs'

@app2.callback(
	Output('graph-button2', 'children'),
	[Input('graph-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(+) Show'


@app.callback(
	Output('graph-container', 'style'),
	[Input('graph-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

@app2.callback(
	Output('graph-container2', 'style'),
	[Input('graph-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app.callback(
    Output('buffer1', 'style'),
    [Input('compute-button', 'n_clicks'),
    Input('url', 'pathname')],
    state=[State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    State('feature_genes', 'value'),
    State('AP_damping_factor', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    State('EPG_beta', 'value'),
    State('disable_EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value')])

def compute_trajectories(n_clicks, pathname, norm, log2, atac, lle_dr, lle_nbs, select,loess_frac,pca_n_PC,pca_first_PC,feature_genes,AP_damping_factor,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_finalenergy,EPG_alpha,EPG_beta,disable_EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['compute-clicks']:

			matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			cell_label_list = []
			if len(cell_label) > 0:
				with open(cell_label[0], 'r') as f:
					for line in f:
						cell_label_list.append(line.strip())

			cell_label_colors_dict = {}
			if len(cell_label_colors) > 0:
				with open(cell_label_colors[0], 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						cell_label_colors_dict[str(line[0])] = str(line[1])

			color_plot = []
			if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
				color_plot = [cell_label_colors_dict[x] for x in cell_label_list]

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--feature_genes':[feature_genes],'--AP_damping_factor':[AP_damping_factor],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_finalenergy':[EPG_finalenergy],'--EPG_alpha':[EPG_alpha],'--EPG_beta':[EPG_beta],'--disable_EPG_collapse':[disable_EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if not param_dict['compute-run']:
				sb.call('python /STREAM/STREAM.py --for_web ' + ' '.join(map(str, arguments_final)) + ' > %s/dummy1.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}

@app.callback(
	Output('custom-loading-states-1', 'style'),
	[Input('compute-button', 'n_clicks'),
	Input('compute-container', 'style'),
	Input('url', 'pathname')])

def update_container(n_clicks, segmentation_container, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton1']:

		return {'display': 'block'}

	elif not param_dict['checkpoint1']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-1', 'interval'),
	[Input('compute-button', 'n_clicks'),
	Input('compute-container', 'style'),
	Input('url', 'pathname')])

def update_container(n_clicks, segmentation_container, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton1']:

		return 5000

	elif not param_dict['checkpoint1']:

		return 5000

	else:

		return 1000000

@app.callback(
    Output('3d-scatter', 'figure'),
    [Input('url', 'pathname')],
    state=[State('compute-button', 'n_clicks')],
    events=[Event('common-interval-1', 'interval')])

def compute_trajectories(pathname, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/dummy1.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/dummy1.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation...\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				cell_label_list = []
				if len(cell_label) > 0:
					with open(cell_label[0], 'r') as f:
						for line in f:
							cell_label_list.append(line.strip())

				cell_label_colors_dict = {}
				if len(cell_label_colors) > 0:
					with open(cell_label_colors[0], 'r') as f:
						for line in f:
							line = line.strip().split('\t')
							cell_label_colors_dict[str(line[1])] = str(line[0])

				color_plot = 0
				if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
					color_plot = 1

				param_dict['compute-clicks'] = n_clicks
				param_dict['checkbutton1'] += 1
				param_dict['checkpoint1'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

				cell_coords = RESULTS_FOLDER + '/coord_cells.csv'
				path_coords = glob.glob(RESULTS_FOLDER + '/coord_curve*csv')

				x = []
				y = []
				z = []
				c = []
				labels = []
				with open(cell_coords, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						c.append(str(line[0]))
						x.append(float(line[1]))
						y.append(float(line[2]))
						z.append(float(line[3]))
						try:
							labels.append(cell_label_colors_dict[str(line[0])])
						except:
							pass

				cell_types = {}
				if color_plot == 0:
					cell_types['single-cell mappings'] = [x, y, z, cell_label_list, 'grey']
				else:
					for label, x_c, y_c, z_c, color in zip(labels, x, y, z, c):
						if label not in cell_types:
							cell_types[label] = [[],[],[],[],[]]
						cell_types[label][0].append(x_c)
						cell_types[label][1].append(y_c)
						cell_types[label][2].append(z_c)
						cell_types[label][3].append(label)
						cell_types[label][4].append(color)

				traces = []
				for label in cell_types:
					traces.append(
						go.Scatter3d(
									x=cell_types[label][0],
									y=cell_types[label][1],
									z=cell_types[label][2],
									mode='markers',
									opacity = 0.5,
									name = label,
									text = cell_types[label][3],
									marker = dict(
										size = 5,
										color = cell_types[label][4]
										)
								)
							)

				roots = []
				for path in path_coords:
					x_p = []
					y_p = []
					z_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					roots.append(s1)
					roots.append(s2)
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))
							z_p.append(float(line[2]))
						traces.append(

							go.Scatter3d(
									    x=x_p, y=y_p, z=z_p,
									    # text = [s1, s2],
									    mode = 'lines',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width=10
									    ),
									)

							)

				roots = sorted(list(set(roots)))

				df = pd.read_table(matrix[0])
				sg_genes = list(np.unique(df.iloc[:,0].values))
				param_dict['starting-nodes'] = roots
				param_dict['compute-run'] = True
				param_dict['sg-genes'] = sg_genes

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            scene = dict(
                    xaxis = dict(showgrid = False, zeroline=True, title = 'Dim.1', ticks='', showticklabels=False),
                    yaxis = dict(showgrid = False, zeroline=True, title = 'Dim.2', ticks='', showticklabels=False),
                    zaxis = dict(showgrid = False, zeroline=True, title = 'Dim.3', ticks='', showticklabels=False))
        )
    }

@app2.callback(
    Output('3d-scatter2', 'figure'),
    [Input('precomp-dataset', 'value')])

def compute_trajectories(dataset):

	traces = []

	cell_label = '/STREAM/%s/cell_labels.tsv' % dataset
	cell_label_colors = '/STREAM/%s/cell_label_colors.tsv' % dataset

	cell_label_list = []
	with open(cell_label, 'r') as f:
		for line in f:
			cell_label_list.append(line.strip())

	cell_label_colors_dict = {}
	with open(cell_label_colors, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			cell_label_colors_dict[str(line[1])] = str(line[0])

	color_plot = 0
	if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		color_plot = 1

	cell_coords = '/STREAM/%s/coord_cells.csv' % dataset
	path_coords = glob.glob('/STREAM/%s/coord_curve*csv' % dataset)

	x = []
	y = []
	z = []
	c = []
	labels = []
	with open(cell_coords, 'r') as f:
		next(f)
		for line in f:
			line = line.strip().split('\t')
			c.append(str(line[0]))
			x.append(float(line[1]))
			y.append(float(line[2]))
			z.append(float(line[3]))
			try:
				labels.append(cell_label_colors_dict[str(line[0])])
			except:
				pass

	cell_types = {}
	if color_plot == 0:
		cell_types['single-cell mappings'] = [x, y, z, cell_label_list, 'grey']
	else:
		for label, x_c, y_c, z_c, color in zip(labels, x, y, z, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(z_c)
			cell_types[label][3].append(label)
			cell_types[label][4].append(color)

	for label in cell_types:
		traces.append(
			go.Scatter3d(
						x=cell_types[label][0],
						y=cell_types[label][1],
						z=cell_types[label][2],
						mode='markers',
						opacity = 0.5,
						name = label,
						text = cell_types[label][3],
						marker = dict(
							size = 5,
							color = cell_types[label][4]
							)
					)
				)

	roots = []
	print path_coords
	for path in path_coords:
		x_p = []
		y_p = []
		z_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		roots.append(s1)
		roots.append(s2)
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))
				z_p.append(float(line[2]))
			traces.append(

				go.Scatter3d(
						    x=x_p, y=y_p, z=z_p,
						    # text = [s1, s2],
						    mode = 'lines',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width=10
						    ),
						)

				)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            scene = dict(
                    xaxis = dict(showgrid = False, zeroline=True, title = 'Dim.1', ticks='', showticklabels=False),
                    yaxis = dict(showgrid = False, zeroline=True, title = 'Dim.2', ticks='', showticklabels=False),
                    zaxis = dict(showgrid = False, zeroline=True, title = 'Dim.3', ticks='', showticklabels=False))
        )
    }

@app.callback(
    Output('flat-tree-scatter', 'figure'),
    [Input('url', 'pathname'),
    Input('3d-scatter', 'figure')],
    state=[State('compute-button', 'n_clicks')],)
    # events=[Event('common-interval-1', 'interval')])

def compute_trajectories(pathname, threed_scatter, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/dummy1.txt'):

			f = open(RESULTS_FOLDER + '/dummy1.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation...\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				cell_label_list = []
				if len(cell_label) > 0:
					with open(cell_label[0], 'r') as f:
						for line in f:
							cell_label_list.append(line.strip())

				cell_label_colors_dict = {}
				if len(cell_label_colors) > 0:
					with open(cell_label_colors[0], 'r') as f:
						for line in f:
							line = line.strip().split('\t')
							cell_label_colors_dict[str(line[1])] = str(line[0])

				color_plot = 0
				if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
					color_plot = 1

				cell_coords = RESULTS_FOLDER + '/flat_tree_coord_cells.csv'
				nodes = RESULTS_FOLDER + '/nodes.tsv'
				edges = RESULTS_FOLDER + '/edges.tsv'

				node_list = {}
				edge_list = []

				with open(nodes, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						node_list[str(line[0])] = [float(line[1]), float(line[2])]

				with open(edges, 'r') as f:
					for line in f:
						line = line.strip().split('\t')
						edge_list.append([str(line[0]), str(line[1])])

				path_coords = {}
				for edge in edge_list:
					edge_name = '-'.join(map(str, edge))
					x_values = [node_list[edge[0]][0], node_list[edge[1]][0]]
					y_values = [node_list[edge[0]][1], node_list[edge[1]][1]]
					path_coords[edge_name] = [x_values, y_values]

				traces = []
				for path in path_coords:
					path_name = path
					x_p = path_coords[path][0]
					y_p = path_coords[path][1]

					text_tmp = [path.split('-')[0], path.split('-')[1]]

					traces.append(

						go.Scatter(
								    x=x_p, y=y_p,
								    text = text_tmp,
								    mode = 'lines+markers+text',
								    opacity = 0.7,
								    name = path_name,
								    line=dict(
								        width=7
								    ),
								    textfont=dict(
										size = 20
									)
								)
						)

				x = []
				y = []
				c = []
				labels = []
				with open(cell_coords, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						c.append(str(line[0]))
						x.append(float(line[1]))
						y.append(float(line[2]))
						try:
							labels.append(cell_label_colors_dict[str(line[0])])
						except:
							pass

				cell_types = {}
				if color_plot == 0:
					cell_types['single-cell mappings'] = [x, y, z, cell_label_list, 'grey']
				else:
					for label, x_c, y_c, color in zip(labels, x, y, c):
						if label not in cell_types:
							cell_types[label] = [[],[],[],[]]
						cell_types[label][0].append(x_c)
						cell_types[label][1].append(y_c)
						cell_types[label][2].append(label)
						cell_types[label][3].append(color)

				for label in cell_types:
					traces.append(

						go.Scatter(
								x=cell_types[label][0],
								y=cell_types[label][1],
								mode='markers',
								opacity = 0.6,
								name = label,
								text = cell_types[label][2],
								marker = dict(
									size = 6,
									color = cell_types[label][3]
									)
								)
							)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app2.callback(
    Output('flat-tree-scatter2', 'figure'),
    [Input('precomp-dataset', 'value')])

def compute_trajectories(dataset):

	traces = []

	cell_label = '/STREAM/%s/cell_labels.tsv' % dataset
	cell_label_colors = '/STREAM/%s/cell_label_colors.tsv' % dataset

	cell_label_list = []
	with open(cell_label, 'r') as f:
		for line in f:
			cell_label_list.append(line.strip())

	cell_label_colors_dict = {}
	with open(cell_label_colors, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			cell_label_colors_dict[str(line[1])] = str(line[0])

	color_plot = 0
	if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		color_plot = 1

	cell_coords = '/STREAM/%s/flat_tree_coord_cells.csv' % dataset
	nodes = '/STREAM/%s/nodes.tsv' % dataset
	edges = '/STREAM/%s/edges.tsv' % dataset

	node_list = {}
	edge_list = []

	with open(nodes, 'r') as f:
		next(f)
		for line in f:
			line = line.strip().split('\t')
			node_list[str(line[0])] = [float(line[1]), float(line[2])]

	with open(edges, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			edge_list.append([str(line[0]), str(line[1])])

	path_coords = {}
	for edge in edge_list:
		edge_name = '-'.join(map(str, edge))
		x_values = [node_list[edge[0]][0], node_list[edge[1]][0]]
		y_values = [node_list[edge[0]][1], node_list[edge[1]][1]]
		path_coords[edge_name] = [x_values, y_values]

	for path in path_coords:
		path_name = path
		x_p = path_coords[path][0]
		y_p = path_coords[path][1]

		text_tmp = [path.split('-')[0], path.split('-')[1]]

		traces.append(

			go.Scatter(
					    x=x_p, y=y_p,
					    text = text_tmp,
					    mode = 'lines+markers+text',
					    opacity = 0.7,
					    name = path_name,
					    line=dict(
					        width=7
					    ),
					    textfont=dict(
							size = 20
						)
					)
			)

	x = []
	y = []
	c = []
	labels = []
	with open(cell_coords, 'r') as f:
		next(f)
		for line in f:
			line = line.strip().split('\t')
			c.append(str(line[0]))
			x.append(float(line[1]))
			y.append(float(line[2]))
			try:
				labels.append(cell_label_colors_dict[str(line[0])])
			except:
				pass

	cell_types = {}
	if color_plot == 0:
		cell_types['single-cell mappings'] = [x, y, z, cell_label_list, 'grey']
	else:
		for label, x_c, y_c, color in zip(labels, x, y, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(label)
			cell_types[label][3].append(color)

	for label in cell_types:
		traces.append(

			go.Scatter(
					x=cell_types[label][0],
					y=cell_types[label][1],
					mode='markers',
					opacity = 0.6,
					name = label,
					text = cell_types[label][2],
					marker = dict(
						size = 6,
						color = cell_types[label][3]
						)
					)
				)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app.callback(
    Output('root', 'options'),
    [Input('3d-scatter', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	return [{'label': i, 'value': i} for i in param_dict['starting-nodes']]

@app2.callback(
    Output('root2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	node_list_tmp = glob.glob('/STREAM/%s/S*' % dataset)

	node_list = [x.split('/')[-1] for x in node_list_tmp if len(x.split('/')[-1]) == 2]

	return [{'label': i, 'value': i} for i in node_list]

@app.callback(
    Output('2d-subway', 'figure'),
    [Input('root', 'value'),
    Input('3d-scatter', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(root, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	cell_coords = RESULTS_FOLDER + '/%s/subway_coord_cells.csv' % root
	path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)

	cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
	cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

	cell_label_list = []
	if len(cell_label) > 0:
		with open(cell_label[0], 'r') as f:
			for line in f:
				cell_label_list.append(line.strip())

	cell_label_colors_dict = {}
	if len(cell_label_colors) > 0:
		with open(cell_label_colors[0], 'r') as f:
			for line in f:
				line = line.strip().split('\t')
				cell_label_colors_dict[str(line[1])] = str(line[0])

	color_plot = 0
	if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		color_plot = 1

	traces = []
	for path in path_coords:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x=x_p, y=y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width=7
						    ),
						    textfont=dict(
								size = 20
							)
						)
				)

	x = []
	y = []
	c = []
	labels = []

	try:
		with open(cell_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x.append(float(line[1]))
				y.append(float(line[2]))
				try:
					labels.append(cell_label_colors_dict[str(line[0])])
				except:
					pass
	except:
		pass

	cell_types = {}
	if color_plot == 0:
		cell_types['single-cell mappings'] = [x, y, cell_label_list, 'grey']
	else:
		for label, x_c, y_c, color in zip(labels, x, y, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(label)
			cell_types[label][3].append(color)

	for label in cell_types:
		traces.append(
			go.Scatter(
						x=cell_types[label][0],
						y=cell_types[label][1],
						mode='markers',
						opacity = 0.6,
						name = label,
						text = cell_types[label][2],
						marker = dict(
							size = 6,
							color = cell_types[label][3]
							)
					)
				)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app2.callback(
    Output('2d-subway2', 'figure'),
    [Input('root2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, dataset):

	cell_coords = '/STREAM/%s/%s/subway_coord_cells.csv' % (dataset, root)
	path_coords = glob.glob('/STREAM/%s/%s/subway_coord_line*csv' % (dataset, root))

	cell_label = '/STREAM/%s/cell_labels.tsv' % dataset
	cell_label_colors = '/STREAM/%s/cell_label_colors.tsv' % dataset

	cell_label_list = []
	with open(cell_label, 'r') as f:
		for line in f:
			cell_label_list.append(line.strip())

	cell_label_colors_dict = {}
	with open(cell_label_colors, 'r') as f:
		for line in f:
			line = line.strip().split('\t')
			cell_label_colors_dict[str(line[1])] = str(line[0])

	color_plot = 0
	if len(cell_label_list) > 0 and len(cell_label_colors_dict) > 0:
		color_plot = 1

	traces = []
	for path in path_coords:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x=x_p, y=y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width=7
						    ),
						    textfont=dict(
								size = 20
							)
						)
				)

	x = []
	y = []
	c = []
	labels = []

	try:
		with open(cell_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x.append(float(line[1]))
				y.append(float(line[2]))
				try:
					labels.append(cell_label_colors_dict[str(line[0])])
				except:
					pass
	except:
		pass

	cell_types = {}
	if color_plot == 0:
		cell_types['single-cell mappings'] = [x, y, cell_label_list, 'grey']
	else:
		for label, x_c, y_c, color in zip(labels, x, y, c):
			if label not in cell_types:
				cell_types[label] = [[],[],[],[]]
			cell_types[label][0].append(x_c)
			cell_types[label][1].append(y_c)
			cell_types[label][2].append(label)
			cell_types[label][3].append(color)

	for label in cell_types:
		traces.append(
			go.Scatter(
						x=cell_types[label][0],
						y=cell_types[label][1],
						mode='markers',
						opacity = 0.6,
						name = label,
						text = cell_types[label][2],
						marker = dict(
							size = 6,
							color = cell_types[label][3]
							)
					)
				)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app.callback(
    Output('rainbow-plot', 'src'),
    [Input('root', 'value'),
    Input('2d-subway', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(root, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	try:

		rainbow_plot = RESULTS_FOLDER + '/%s/stream_plot.png' % root
		rainbow_plot_image = base64.b64encode(open(rainbow_plot, 'rb').read())

		return 'data:image/png;base64,{}'.format(rainbow_plot_image)

	except:
		pass

@app2.callback(
    Output('rainbow-plot2', 'src'),
    [Input('root2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, dataset):

	try:

		rainbow_plot = '/STREAM/%s/%s/stream_plot.png' % (dataset, root)
		rainbow_plot_image = base64.b64encode(open(rainbow_plot, 'rb').read())

		return 'data:image/png;base64,{}'.format(rainbow_plot_image)

	except:
		pass

############################# SINGLE GENE VISUALIZATION #############################
@app.callback(
	Output('sg-plot-button', 'children'),
	[Input('sg-plot-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graph'
	else:
		return '(-) Hide Graph'

@app2.callback(
	Output('sg-plot-button2', 'children'),
	[Input('sg-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(+) Show'

@app.callback(
	Output('sg-plot-container', 'style'),
	[Input('sg-plot-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

@app2.callback(
	Output('sg-plot-container2', 'style'),
	[Input('sg-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app.callback(
    Output('sg-gene', 'options'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return [{'label': i, 'value': i} for i in param_dict['sg-genes']]

@app2.callback(
    Output('sg-gene2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	gene_list_tmp = glob.glob('/STREAM/%s/S0/stream_plot_*png' % dataset)

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	return [{'label': i, 'value': i} for i in gene_list]

@app.callback(
    Output('sg-gene', 'value'),
    [Input('sg-gene', 'options'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return param_dict['sg-genes'][0]

@app.callback(
    Output('sg-compute', 'children'),
    [Input('sg-compute', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['sg-clicks'] and param_dict['compute-run']:
			return 'Running...'
		else:
			return 'Perform Analysis'

	else:
		return 'Perform Analysis'

@app.callback(
    Output('sg-container', 'style'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
    Output('sg-button', 'disabled'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:

			if n_clicks > param_dict['sg-clicks']:
				return True
			else:
				return False

		else:
			return True

	return True

@app.callback(
    Output('sg-button', 'children'),
    [Input('sg-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:
			return 'Get Started'
		elif not param_dict['compute-run']:
			return 'Complete Step 2'

	else:
		return 'Complete Step 2'

@app.callback(
    Output('buffer2', 'style'),
    [Input('sg-compute', 'n_clicks'),
    Input('url', 'pathname')],
    state=[State('root', 'value'),
    State('sg-gene', 'value'),
    State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    State('feature_genes', 'value'),
    State('AP_damping_factor', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    State('EPG_beta', 'value'),
    State('disable_EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value')])

def compute_single_gene(n_clicks, pathname, root, gene, norm, log2, atac, lle_dr, lle_nbs, select, loess_frac,pca_n_PC,pca_first_PC,feature_genes,AP_damping_factor,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_finalenergy,EPG_alpha,EPG_beta,disable_EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if (n_clicks > param_dict['sg-clicks'] or param_dict['sg-gene'] != gene):

			matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--feature_genes':[feature_genes],'--AP_damping_factor':[AP_damping_factor],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_finalenergy':[EPG_finalenergy],'--EPG_alpha':[EPG_alpha],'--EPG_beta':[EPG_beta],'--disable_EPG_collapse':[disable_EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if param_dict['compute-run']:
				sb.call('python /STREAM/STREAM.py --for_web -p -g %s ' % gene + ' '.join(map(str, arguments_final)) + ' > %s/dummy2.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}


@app.callback(
	Output('custom-loading-states-2', 'style'),
	[Input('sg-compute', 'n_clicks'),
	Input('2d-subway-sg', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton2']:

		return {'display': 'block'}

	elif not param_dict['checkpoint2']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-2', 'interval'),
	[Input('sg-compute', 'n_clicks'),
	Input('2d-subway-sg', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton2']:

		return 5000

	elif not param_dict['checkpoint2']:

		return 5000

	else:

		return 1000000

@app.callback(
    Output('2d-subway-sg', 'figure'),
    [Input('url', 'pathname')],
    state=[State('sg-compute', 'n_clicks'),
    State('root', 'value'),
    State('sg-gene', 'value')],
    events=[Event('common-interval-2', 'interval')])

def compute_trajectories(pathname, n_clicks, root, gene):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/dummy2.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/dummy2.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation...\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				cell_coords = RESULTS_FOLDER + '/%s/subway_coord_cells.csv' % root
				gene_coords = RESULTS_FOLDER + '/%s/subway_coord_%s.csv' % (root, gene)
				path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)
				genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
				genes = [x.split('_')[-1].strip('.csv') for x in genes]

				traces = []
				for path in path_coords:
					x_p = []
					y_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))

						if len(x_p) == 2:
							text_tmp = [s1, s2]
						elif len(x_p) == 4:
							text_tmp = [s1, None, None, s2]
						elif len(x_p) == 6:
							text_tmp = [s1, None, None, None, None, s2]

						traces.append(

							go.Scatter(
									    x = x_p, y = y_p,
									    text = text_tmp,
									    mode = 'lines+markers+text',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width = 3,
									        color = 'grey'
									    ),
									    textfont=dict(
											size = 20
										)
									)
							)

				x_c = []
				y_c = []
				c = []
				exp = []
				exp_scaled = []

				# try:
				with open(gene_coords, 'r') as f:
					next(f)
					for line in f:
						line = line.strip().split('\t')
						c.append(str(line[0]))
						x_c.append(float(line[1]))
						y_c.append(float(line[2]))
						exp_scaled.append(float(line[3]))
						# exp_scaled.append(float(line[4]))
				# except:
				# 	pass

				exp_labels = ['Expression: ' + str(x) for x in exp]
				traces.append(
					go.Scatter(
								x = x_c,
								y = y_c,
								mode='markers',
								opacity = 0.6,
								name = 'single-cell mappings',
								text = exp_labels,
								marker = dict(
									size = 6,
									color = exp_scaled,
									colorscale = 'RdBu'
									)
							)
						)

				param_dict['sg-clicks'] = n_clicks
				param_dict['sg-gene'] = gene
				param_dict['sg-run'] = True
				param_dict['checkbutton2'] += 1
				param_dict['checkpoint2'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app2.callback(
    Output('2d-subway-sg2', 'figure'),
    [Input('precomp-dataset', 'value'),
    Input('sg-gene2', 'value'),
    Input('root2', 'value')])

def compute_trajectories(dataset, gene, root):

	traces = []

	cell_coords = '/STREAM/%s/%s/subway_coord_cells.csv' % (dataset, root)
	path_coords = glob.glob('/STREAM/%s/%s/subway_coord_line*csv' % (dataset, root))
	gene_coords = '/STREAM/%s/%s/subway_coord_%s.csv' % (dataset, root, gene)

	cell_label = '/STREAM/%s/cell_labels.tsv' % dataset
	cell_label_colors = '/STREAM/%s/cell_label_colors.tsv' % dataset

	traces = []
	for path in path_coords:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x = x_p, y = y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width = 3,
						        color = 'grey'
						    ),
						    textfont=dict(
								size = 20
							)
						)
				)

	x_c = []
	y_c = []
	c = []
	exp = []
	exp_scaled = []

	try:
		with open(gene_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x_c.append(float(line[1]))
				y_c.append(float(line[2]))
				exp_scaled.append(float(line[3]))
				# exp_scaled.append(float(line[4]))
	except:
		pass

	exp_labels = ['Expression: ' + str(x) for x in exp]
	traces.append(
		go.Scatter(
					x = x_c,
					y = y_c,
					mode='markers',
					opacity = 0.6,
					name = 'single-cell mappings',
					text = exp_labels,
					marker = dict(
						size = 6,
						color = exp_scaled,
						colorscale = 'RdBu'
						)
				)
			)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }


@app.callback(
    Output('sg-plot', 'src'),
    [Input('2d-subway-sg', 'figure'),
    Input('url', 'pathname')],
    state=[State('root', 'value'),
    State('sg-gene', 'value')])

def num_clicks_compute(figure, pathname, root, gene):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
		genes = [x for x in genes if len(x.split('_')) == 4]
		genes = [x.split('_')[3].strip('.csv') for x in genes]

		if gene != 'False':

			try:

				discovery_plot = RESULTS_FOLDER + '/%s/stream_plot_%s.png' % (root, gene)
				discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read())

				return 'data:image/png;base64,{}'.format(discovery_plot_image)

			except:

				pass

@app2.callback(
    Output('sg-plot2', 'src'),
    [Input('precomp-dataset', 'value'),
    Input('sg-gene2', 'value'),
    Input('root2', 'value')])

def num_clicks_compute(dataset, gene, root):

	try:

		discovery_plot = '/STREAM/%s/%s/stream_plot_%s.png' % (dataset, root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read())
		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:

		pass

######################################## GENE DISCOVERY ########################################
@app.callback(
	Output('discovery-plot-button', 'children'),
	[Input('discovery-plot-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graph'
	else:
		return '(-) Hide Graph'

@app2.callback(
	Output('discovery-plot-button2', 'children'),
	[Input('discovery-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(+) Show'

@app.callback(
	Output('discovery-plot-container', 'style'),
	[Input('discovery-plot-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

@app2.callback(
	Output('discovery-plot-container2', 'style'),
	[Input('discovery-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app.callback(
    Output('discovery-gene', 'options'),
    [Input('2d-subway-discovery', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return [{'label': i, 'value': i} for i in param_dict['discovery-genes']]

@app2.callback(
    Output('discovery-gene2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	gene_list_tmp = glob.glob('/STREAM/%s/S0/stream_plot_*png' % dataset)

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	return [{'label': i, 'value': i} for i in gene_list]

@app.callback(
    Output('discovery-container', 'style'),
    [Input('2d-subway-discovery', 'figure'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['discovery-clicks'] > 0:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
    Output('discovery-button', 'disabled'),
    [Input('discovery-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:

			if n_clicks > param_dict['discovery-clicks']:
				return True
			else:
				return False

		else:
			return True

	else:
		return True

@app.callback(
    Output('discovery-button', 'children'),
    [Input('discovery-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['discovery-clicks'] and param_dict['compute-run']:
			return 'Running...'
		elif param_dict['compute-run']:
			return 'Perform Analysis'
		elif not param_dict['compute-run']:
			return 'Complete Step 2'

	else:
		return 'Complete Step 2'

@app.callback(
    Output('buffer3', 'style'),
    [Input('discovery-button', 'n_clicks'),
    Input('url', 'pathname')],
    state = [State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    State('feature_genes', 'value'),
    State('AP_damping_factor', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    State('EPG_beta', 'value'),
    State('disable_EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value'),
    State('root', 'value'),
    State('discovery-gene', 'value')])

def compute_discovery(n_clicks, pathname, norm, log2, atac, lle_dr, lle_nbs, select,loess_frac,pca_n_PC,pca_first_PC,feature_genes,AP_damping_factor,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_finalenergy,EPG_alpha,EPG_beta,disable_EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par,root,gene):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['discovery-clicks'] or param_dict['discovery-gene'] != gene:

			matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--feature_genes':[feature_genes],'--AP_damping_factor':[AP_damping_factor],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_finalenergy':[EPG_finalenergy],'--EPG_alpha':[EPG_alpha],'--EPG_beta':[EPG_beta],'--disable_EPG_collapse':[disable_EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if not param_dict['discovery-run']:
				sb.call('python /STREAM/STREAM.py --for_web -d ' + ' '.join(map(str, arguments_final)) + ' > %s/dummy3.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}

@app.callback(
	Output('custom-loading-states-3', 'style'),
	[Input('discovery-button', 'n_clicks'),
	Input('2d-subway-discovery', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton3']:

		return {'display': 'block'}

	elif not param_dict['checkpoint3']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-3', 'interval'),
	[Input('discovery-button', 'n_clicks'),
	Input('2d-subway-discovery', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton3']:

		return 5000

	elif not param_dict['checkpoint3']:

		return 5000

	else:

		return 1000000

@app.callback(
    Output('2d-subway-discovery', 'figure'),
    [Input('url', 'pathname'),
    Input('root', 'value'),
    Input('discovery-gene', 'value')],
    state=[State('discovery-button', 'n_clicks')],
    events=[Event('common-interval-3', 'interval')])

def compute_trajectories(pathname, root, gene, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/dummy3.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/dummy3.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation...\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				cell_coords = RESULTS_FOLDER + '/%s/subway_coord_cells.csv' % root
				gene_coords = RESULTS_FOLDER + '/%s/subway_coord_%s.csv' % (root, gene)
				path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)
				genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
				genes = [x.split('_')[-1].strip('.csv') for x in genes]

				param_dict['discovery-genes'] = [x for x in genes if x in param_dict['sg-genes']]

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

				traces = []
				for path in path_coords:
					x_p = []
					y_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))

						if len(x_p) == 2:
							text_tmp = [s1, s2]
						elif len(x_p) == 4:
							text_tmp = [s1, None, None, s2]
						elif len(x_p) == 6:
							text_tmp = [s1, None, None, None, None, s2]

						traces.append(

							go.Scatter(
									    x = x_p, y = y_p,
									    text = text_tmp,
									    mode = 'lines+markers+text',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width = 3,
									        color = 'grey'
									    ),
									    textfont=dict(
											size = 20
										)
									)

							)

				x_c = []
				y_c = []
				c = []
				exp = []
				exp_scaled = []

				try:
					with open(gene_coords, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							c.append(str(line[0]))
							x_c.append(float(line[1]))
							y_c.append(float(line[2]))
							exp_scaled.append(float(line[3]))
							# exp_scaled.append(float(line[4]))
				except:
					pass

				exp_labels = ['Expression: ' + str(x) for x in exp]
				traces.append(
					go.Scatter(
								x = x_c,
								y = y_c,
								mode='markers',
								opacity = 0.6,
								name = 'single-cell mappings',
								text = exp_labels,
								marker = dict(
									size = 6,
									color = exp_scaled,
									colorscale = 'RdBu'
									)
							)
						)

				param_dict['discovery-clicks'] = n_clicks
				param_dict['discovery-gene'] = gene
				param_dict['discovery-run'] = True
				param_dict['checkbutton3'] += 1
				param_dict['checkpoint3'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app2.callback(
    Output('2d-subway-discovery2', 'figure'),
    [Input('precomp-dataset', 'value'),
    Input('root2', 'value'),
    Input('discovery-gene2', 'value')])

def compute_trajectories(dataset, root, gene):

	traces = []

	cell_coords = '/STREAM/%s/%s/subway_coord_cells.csv' % (dataset, root)
	path_coords = glob.glob('/STREAM/%s/%s/subway_coord_line*csv' % (dataset, root))
	gene_coords = '/STREAM/%s/%s/subway_coord_%s.csv' % (dataset, root, gene)

	cell_label = '/STREAM/%s/cell_labels.tsv' % dataset
	cell_label_colors = '/STREAM/%s/cell_label_colors.tsv' % dataset

	for path in path_coords:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x = x_p, y = y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width = 3,
						        color = 'grey'
						    ),
						    textfont=dict(
								size = 20
							)
						)

				)

	x_c = []
	y_c = []
	c = []
	exp = []
	exp_scaled = []

	try:
		with open(gene_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x_c.append(float(line[1]))
				y_c.append(float(line[2]))
				exp_scaled.append(float(line[3]))
				# exp_scaled.append(float(line[4]))
	except:
		pass

	exp_labels = ['Expression: ' + str(x) for x in exp]
	traces.append(
		go.Scatter(
					x = x_c,
					y = y_c,
					mode='markers',
					opacity = 0.6,
					name = 'single-cell mappings',
					text = exp_labels,
					marker = dict(
						size = 6,
						color = exp_scaled,
						colorscale = 'RdBu'
						)
				)
			)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app.callback(
    Output('discovery-plot', 'src'),
    [Input('root', 'value'),
    Input('discovery-gene', 'value'),
    Input('url', 'pathname')])

def num_clicks_compute(root, gene, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if gene != 'False':

			try:

				discovery_plot = RESULTS_FOLDER + '/%s/stream_plot_%s.png' % (root, gene)
				discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read())

				return 'data:image/png;base64,{}'.format(discovery_plot_image)

			except:
				pass

@app2.callback(
    Output('discovery-plot2', 'src'),
    [Input('root2', 'value'),
    Input('discovery-gene2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, gene, dataset):

	try:

		discovery_plot = '/STREAM/%s/%s/stream_plot_%s.png' % (dataset, root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read())

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app.callback(
    Output('de-branches', 'options'),
    [Input('2d-subway-discovery', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		combined_branches = []
		find_tables = glob.glob(RESULTS_FOLDER + '/DE_Genes/*.tsv')
		for table in find_tables:
			branch1 = table.split(' and ')[0].split('genes_')[1]
			branch2 = table.split(' and ')[1].strip('.tsv')

			combined_branch = branch1 + ' and ' + branch2

			if combined_branch not in combined_branches:
				combined_branches.append(combined_branch)

		return [{'label': i, 'value': i} for i in combined_branches]

@app2.callback(
    Output('de-branches2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	combined_branches = []
	find_tables = glob.glob('/STREAM/%s/DE_Genes/*.tsv' % dataset)
	for table in find_tables:
		branch1 = table.split(' and ')[0].split('genes_')[1]
		branch2 = table.split(' and ')[1].strip('.tsv')

		combined_branch = branch1 + ' and ' + branch2

		if combined_branch not in combined_branches:
			combined_branches.append(combined_branch)

	return [{'label': i, 'value': i} for i in combined_branches]

@app.callback(
    Output('de-direction', 'options'),
    [Input('de-branches', 'value')])

def num_clicks_compute(branches):

	try:
		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		branches = [branch1, branch2]
	except:
		branches = ['Choose branch pair above']
		pass

	return [{'label': i, 'value': i} for i in branches]

@app2.callback(
    Output('de-direction2', 'options'),
    [Input('de-branches2', 'value')])

def num_clicks_compute(branches):

	try:
		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		branches = [branch1, branch2]
	except:
		branches = ['Choose branch pair above']
		pass

	return [{'label': i, 'value': i} for i in branches]

@app.callback(
	Output('discovery-table', 'children'),
	[Input('de-slider', 'value'),
	Input('de-branches', 'value'),
	Input('de-direction', 'value'),
	Input('2d-subway-discovery', 'figure'),
	Input('url', 'pathname')])

def update_table(slider, branches, direction, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	use_this_table = ''

	try:

		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]

		if direction == branch1:
			direction_classify = '_up_'
		elif direction == branch2:
			direction_classify = '_down_'

		find_table = glob.glob(RESULTS_FOLDER + '/DE_Genes/*.tsv')
		for table in find_table:
			if (branch1 in table) and (branch2 in table) and (direction_classify in table):
				use_this_table = table
				break
	except:
		pass

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','z_score','U','diff','mean_up','mean_down','pval','qval']
		dff = df.head(n = slider)[['gene', 'pval', 'qval']] # update with your own logic

		return generate_table(dff)

@app2.callback(
	Output('discovery-table2', 'children'),
	[Input('de-slider2', 'value'),
	Input('de-branches2', 'value'),
	Input('de-direction2', 'value'),
	Input('precomp-dataset', 'value')])

def update_table(slider, branches, direction, dataset):

	use_this_table = ''

	try:

		branch1 = branches.split(' and ')[0]
		branch2 = branches.split(' and ')[1]
		
		if direction == branch1:
			direction_classify = '_up_'
		elif direction == branch2:
			direction_classify = '_down_'

		find_table = glob.glob('/STREAM/%s/DE_Genes/*.tsv' % dataset)
		for table in find_table:
			if (branch1 in table) and (branch2 in table) and (direction_classify in table):
				use_this_table = table
				break
	except:
		pass

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','z_score','U','diff','mean_up','mean_down','pval','qval']
		dff = df.head(n = slider)[['gene', 'pval', 'qval']] # update with your own logic

		return generate_table(dff)

### GENE CORRELATION
@app.callback(
	Output('correlation-plot-button', 'children'),
	[Input('correlation-plot-button', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(+) Show Graph'
	else:
		return '(-) Hide Graph'

@app2.callback(
	Output('correlation-plot-button2', 'children'),
	[Input('correlation-plot-button2', 'n_clicks')])

def update_score_params_button(n_clicks):

	if n_clicks%2 != 0:
		return '(-) Hide'
	else:
		return '(-) Show'

@app.callback(
	Output('correlation-plot-container', 'style'),
	[Input('correlation-plot-button', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'none'}
	else:
		return {'display': 'block'}

@app2.callback(
	Output('correlation-plot-container2', 'style'),
	[Input('correlation-plot-button2', 'n_clicks')])

def update_score_params_visual(n_clicks):

	if n_clicks%2 != 0:
		return {'display': 'block'}
	else:
		return {'display': 'none'}

@app.callback(
    Output('correlation-gene', 'options'),
    [Input('2d-subway-correlation', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		return [{'label': i, 'value': i} for i in param_dict['correlation-genes']]

@app2.callback(
    Output('correlation-gene2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	gene_list_tmp = glob.glob('/STREAM/%s/S0/stream_plot_*png' % dataset)

	gene_list = [x.split('_')[-1].replace('.png', '') for x in gene_list_tmp]

	return [{'label': i, 'value': i} for i in gene_list]

@app.callback(
    Output('correlation-container', 'style'),
    [Input('2d-subway-correlation', 'figure'),
    Input('url', 'pathname')])

def smoothing_container(fig_update, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['correlation-clicks'] > 0:
			return {'display': 'block'}
		else:
			return {'display': 'none'}

	else:
		return {'display': 'none'}

@app.callback(
    Output('correlation-button', 'disabled'),
    [Input('correlation-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if param_dict['compute-run']:

			if n_clicks > param_dict['correlation-clicks']:
				return True
			else:
				return False

		else:
			return True

	else:
		return True

@app.callback(
    Output('correlation-button', 'children'),
    [Input('correlation-button', 'n_clicks'),
    Input('url', 'pathname')],
    events=[Event('common-interval', 'interval')])

def num_clicks_compute(n_clicks, pathname):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['correlation-clicks'] and param_dict['compute-run']:
			return 'Running...'
		elif param_dict['compute-run']:
			return 'Perform Analysis'
		elif not param_dict['compute-run']:
			return 'Complete Step 2'

	else:
		return 'Complete Step 2'

@app.callback(
    Output('buffer4', 'style'),
    [Input('correlation-button', 'n_clicks'),
    Input('url', 'pathname')],
    state = [State('norm', 'value'),
    State('log2', 'value'),
    State('atac', 'value'),
    State('lle-dr', 'value'),
    State('lle-nbs', 'value'),
    State('select', 'value'),
    State('loess_frac', 'value'),
    State('pca_n_PC', 'value'),
    State('pca_first_PC', 'value'),
    State('feature_genes', 'value'),
    State('AP_damping_factor', 'value'),
    State('EPG_n_nodes', 'value'),
    State('EPG_lambda', 'value'),
    State('EPG_mu', 'value'),
    State('EPG_trimmingradius', 'value'),
    State('EPG_finalenergy', 'value'),
    State('EPG_alpha', 'value'),
    State('EPG_beta', 'value'),
    State('disable_EPG_collapse', 'value'),
    State('EPG_collapse_mode', 'value'),
    State('EPG_collapse_par', 'value'),
    State('EPG_shift', 'value'),
    State('EPG_shift_mode', 'value'),
    State('EPG_shift_DR', 'value'),
    State('EPG_shift_maxshift', 'value'),
    State('disable_EPG_ext', 'value'),
    State('EPG_ext_mode', 'value'),
    State('EPG_ext_par', 'value'),
    State('root', 'value'),
    State('correlation-gene', 'value')])

def compute_correlation(n_clicks, pathname, norm, log2, atac, lle_dr, lle_nbs, select,loess_frac,pca_n_PC,pca_first_PC,feature_genes,AP_damping_factor,EPG_n_nodes,EPG_lambda,EPG_mu,EPG_trimmingradius,EPG_finalenergy,EPG_alpha,EPG_beta,disable_EPG_collapse,EPG_collapse_mode,EPG_collapse_par,EPG_shift,EPG_shift_mode,EPG_shift_DR,EPG_shift_maxshift,disable_EPG_ext,EPG_ext_mode,EPG_ext_par,root,gene):

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
			json_string = f.readline().strip()
			param_dict = json.loads(json_string)

		if n_clicks > param_dict['correlation-clicks'] or param_dict['correlation-gene'] != gene:

			matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
			cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
			cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

			arguments = {'-m':[], '-l':[], '-c':[], '-o': [RESULTS_FOLDER], '--norm':[norm], '--log2':[log2], '--atac':[atac], '--lle_components':[lle_dr], '--lle_neighbours':[lle_nbs], '--select_features':[select],
			'--loess_frac':[loess_frac], '--pca_n_PC':[pca_n_PC], '--pca_first_PC':[pca_first_PC],'--feature_genes':[feature_genes],'--AP_damping_factor':[AP_damping_factor],'--EPG_n_nodes':[EPG_n_nodes],
			'--EPG_lambda':[EPG_lambda],'--EPG_mu':[EPG_mu],'--EPG_trimmingradius':[EPG_trimmingradius],'--EPG_finalenergy':[EPG_finalenergy],'--EPG_alpha':[EPG_alpha],'--EPG_beta':[EPG_beta],'--disable_EPG_collapse':[disable_EPG_collapse],
			'--EPG_collapse_mode':[EPG_collapse_mode],'--EPG_collapse_par':[EPG_collapse_par],'--EPG_shift':[EPG_shift],'--EPG_shift_mode':[EPG_shift_mode],'--EPG_shift_DR':[EPG_shift_DR],'--EPG_shift_maxshift':[EPG_shift_maxshift],
			'--disable_EPG_ext':[disable_EPG_ext],'--EPG_ext_mode':[EPG_ext_mode],'--EPG_ext_par':[EPG_ext_par]}

			if len(matrix) > 0:
				arguments['-m'].append(matrix[0])

			if len(cell_label) > 0:
				arguments['-l'].append(cell_label[0])

			if len(cell_label_colors) > 0:
				arguments['-c'].append(cell_label_colors[0])

			arguments_final = []
			for arg in arguments:
				if len(arguments[arg]) > 0:
					if arguments[arg][0] == 'True':
						arguments_final.append(arg)
					elif arguments[arg][0] != 'False' and arguments[arg][0] != None:
						arguments_final.append(arg)
						arguments_final.append(arguments[arg][0])

			if not param_dict['correlation-run']:
				sb.call('python /STREAM/STREAM.py --for_web -t ' + ' '.join(map(str, arguments_final)) + ' > %s/dummy4.txt' % (RESULTS_FOLDER), shell = True)

			return {'display': 'block'}

		else:
			return {'display': 'block'}

	else:
		return {'display': 'block'}

@app.callback(
	Output('custom-loading-states-4', 'style'),
	[Input('correlation-button', 'n_clicks'),
	Input('2d-subway-correlation', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton4']:

		return {'display': 'block'}

	elif not param_dict['checkpoint4']:

		return {'display': 'block'}

	else:

		return {'display': 'none'}

@app.callback(
	Output('common-interval-4', 'interval'),
	[Input('correlation-button', 'n_clicks'),
	Input('2d-subway-correlation', 'figure'),
	Input('url', 'pathname')])

def update_container(n_clicks, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
		json_string = f.readline().strip()
		param_dict = json.loads(json_string)

	if n_clicks == param_dict['checkbutton4']:

		return 5000

	elif not param_dict['checkpoint4']:

		return 5000

	else:

		return 1000000

@app.callback(
    Output('2d-subway-correlation', 'figure'),
    [Input('url', 'pathname'),
    Input('root', 'value'),
    Input('correlation-gene', 'value')],
    state=[State('correlation-button', 'n_clicks')],
    events=[Event('common-interval-4', 'interval')])

def compute_trajectories(pathname, root, gene, n_clicks):

	traces = []

	if pathname:

		UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
		RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

		if os.path.exists(RESULTS_FOLDER + '/dummy4.txt'):

			with open(UPLOADS_FOLDER + '/params.json', 'r') as f:
				json_string = f.readline().strip()
				param_dict = json.loads(json_string)

			f = open(RESULTS_FOLDER + '/dummy4.txt', 'r')
			f_data = f.readlines()
			f.close()

			if 'Finished computation...\n' in f_data:

				matrix = glob.glob(UPLOADS_FOLDER + '/Gene_Expression_Matrix*')
				cell_label = glob.glob(UPLOADS_FOLDER + '/Cell_Labels*')
				cell_label_colors = glob.glob(UPLOADS_FOLDER + '/Cell_Label_Colors*')

				gene_coords = RESULTS_FOLDER + '/%s/subway_coord_%s.csv' % (root, gene)
				path_coords = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_line*csv' % root)
				genes = glob.glob(RESULTS_FOLDER + '/%s/subway_coord_*csv' % root)
				genes = [x.split('_')[-1].strip('.csv') for x in genes]

				param_dict['correlation-genes'] = [x for x in genes if x in param_dict['sg-genes']]

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

				traces = []
				for path in path_coords:
					x_p = []
					y_p = []
					s1 = path.strip().split('_')[-2]
					s2 = path.strip().split('_')[-1].strip('.csv')
					s_3 = [s1, s2]
					path_name = '-'.join(map(str, s_3))
					with open(path, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							x_p.append(float(line[0]))
							y_p.append(float(line[1]))

						if len(x_p) == 2:
							text_tmp = [s1, s2]
						elif len(x_p) == 4:
							text_tmp = [s1, None, None, s2]
						elif len(x_p) == 6:
							text_tmp = [s1, None, None, None, None, s2]

						traces.append(

							go.Scatter(
									    x = x_p, y = y_p,
									    text = text_tmp,
									    mode = 'lines+markers+text',
									    opacity = 0.7,
									    name = path_name,
									    line=dict(
									        width = 3,
									        color = 'grey'
									    ),
									    textfont=dict(
											size = 20
										)
									)

							)

				x_c = []
				y_c = []
				c = []
				exp = []
				exp_scaled = []

				try:
					with open(gene_coords, 'r') as f:
						next(f)
						for line in f:
							line = line.strip().split('\t')
							c.append(str(line[0]))
							x_c.append(float(line[1]))
							y_c.append(float(line[2]))
							exp_scaled.append(float(line[3]))
							# exp_scaled.append(float(line[4]))
				except:
					pass

				exp_labels = ['Expression: ' + str(x) for x in exp]

				traces.append(
					go.Scatter(
								x = x_c,
								y = y_c,
								mode='markers',
								opacity = 0.6,
								name = 'single-cell mappings',
								text = exp_labels,
								marker = dict(
									size = 6,
									color = exp_scaled,
									colorscale = 'RdBu'
									)
							)
						)

				param_dict['correlation-clicks'] = n_clicks
				param_dict['correlation-gene'] = gene
				param_dict['correlation-run'] = True
				param_dict['checkbutton4'] += 1
				param_dict['checkpoint4'] = True

				with open(UPLOADS_FOLDER + '/params.json', 'w') as f:
					new_json_string = json.dumps(param_dict)
					f.write(new_json_string + '\n')

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app2.callback(
    Output('2d-subway-correlation2', 'figure'),
    [Input('precomp-dataset', 'value'),
    Input('root2', 'value'),
    Input('correlation-gene2', 'value')])

def compute_trajectories(dataset, root, gene):

	traces = []

	cell_coords = '/STREAM/%s/%s/subway_coord_cells.csv' % (dataset, root)
	path_coords = glob.glob('/STREAM/%s/%s/subway_coord_line*csv' % (dataset, root))
	gene_coords = '/STREAM/%s/%s/subway_coord_%s.csv' % (dataset, root, gene)

	cell_label = '/STREAM/%s/cell_labels.tsv' % dataset
	cell_label_colors = '/STREAM/%s/cell_label_colors.tsv' % dataset

	traces = []
	for path in path_coords:
		x_p = []
		y_p = []
		s1 = path.strip().split('_')[-2]
		s2 = path.strip().split('_')[-1].strip('.csv')
		s_3 = [s1, s2]
		path_name = '-'.join(map(str, s_3))
		with open(path, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				x_p.append(float(line[0]))
				y_p.append(float(line[1]))

			if len(x_p) == 2:
				text_tmp = [s1, s2]
			elif len(x_p) == 4:
				text_tmp = [s1, None, None, s2]
			elif len(x_p) == 6:
				text_tmp = [s1, None, None, None, None, s2]

			traces.append(

				go.Scatter(
						    x = x_p, y = y_p,
						    text = text_tmp,
						    mode = 'lines+markers+text',
						    opacity = 0.7,
						    name = path_name,
						    line=dict(
						        width = 3,
						        color = 'grey'
						    ),
						    textfont=dict(
								size = 20
							)
						)

				)

	x_c = []
	y_c = []
	c = []
	exp = []
	exp_scaled = []

	try:
		with open(gene_coords, 'r') as f:
			next(f)
			for line in f:
				line = line.strip().split('\t')
				c.append(str(line[0]))
				x_c.append(float(line[1]))
				y_c.append(float(line[2]))
				exp_scaled.append(float(line[3]))
				# exp_scaled.append(float(line[4]))
	except:
		pass

	exp_labels = ['Expression: ' + str(x) for x in exp]

	traces.append(
		go.Scatter(
					x = x_c,
					y = y_c,
					mode='markers',
					opacity = 0.6,
					name = 'single-cell mappings',
					text = exp_labels,
					marker = dict(
						size = 6,
						color = exp_scaled,
						colorscale = 'RdBu'
						)
				)
			)

	return {
        'data': traces,
        'layout': go.Layout(
        	autosize = True,
        	margin=dict(l=0,r=0,b=0,t=0),
            hovermode='closest',
            xaxis = dict(showgrid = False, zeroline=False, title = 'Dim.1'),
            yaxis = dict(showgrid = False, zeroline=False, title = 'Dim.2'),
        )
    }

@app.callback(
    Output('correlation-plot', 'src'),
    [Input('root', 'value'),
    Input('correlation-gene', 'value'),
    Input('url', 'pathname')])

def num_clicks_compute(root, gene, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	if gene != 'False':

		try:

			discovery_plot = RESULTS_FOLDER + '/%s/stream_plot_%s.png' % (root, gene)
			discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read())

			return 'data:image/png;base64,{}'.format(discovery_plot_image)

		except:
			pass

@app2.callback(
    Output('correlation-plot2', 'src'),
    [Input('root2', 'value'),
    Input('correlation-gene2', 'value'),
    Input('precomp-dataset', 'value')])

def num_clicks_compute(root, gene, dataset):

	try:

		discovery_plot = '/STREAM/%s/%s/stream_plot_%s.png' % (dataset, root, gene)
		discovery_plot_image = base64.b64encode(open(discovery_plot, 'rb').read())

		return 'data:image/png;base64,{}'.format(discovery_plot_image)

	except:
		pass

@app.callback(
    Output('corr-branches', 'options'),
    [Input('2d-subway-correlation', 'figure'),
    Input('url', 'pathname')])

def num_clicks_compute(fig_update, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	branches = []
	find_tables = glob.glob(RESULTS_FOLDER + '/Transition_Genes/*.tsv')
	for table in find_tables:
		branch = table.split('_Genes_')[1].strip('.tsv')

		if branch not in branches:
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

@app2.callback(
    Output('corr-branches2', 'options'),
    [Input('precomp-dataset', 'value')])

def num_clicks_compute(dataset):

	branches = []
	find_tables = glob.glob('/STREAM/%s/Transition_Genes/*.tsv' % dataset)
	for table in find_tables:
		branch = table.split('_Genes_')[1].strip('.tsv')

		if branch not in branches:
			branches.append(branch)

	return [{'label': i, 'value': i} for i in branches]

@app.callback(
	Output('correlation-table', 'children'),
	[Input('corr-slider', 'value'),
	Input('corr-branches', 'value'),
	Input('2d-subway-correlation', 'figure'),
	Input('url', 'pathname')])

def update_table(slider, branch, figure, pathname):

	UPLOADS_FOLDER = app.server.config['UPLOADS_FOLDER'] + '/' + str(pathname).split('/')[-1]
	RESULTS_FOLDER = app.server.config['RESULTS_FOLDER'] + '/' + str(pathname).split('/')[-1]

	use_this_table = ''

	find_table = glob.glob(RESULTS_FOLDER + '/Transition_Genes/*.tsv')
	for table in find_table:
		if branch in table:
			use_this_table = table
			break

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','stat','diff','pval','qval']
		dff = df.head(n = slider)[['gene', 'pval', 'qval']] # update with your own logic

		return generate_table(dff)

@app2.callback(
	Output('correlation-table2', 'children'),
	[Input('corr-slider2', 'value'),
	Input('corr-branches2', 'value'),
	Input('precomp-dataset', 'value')])

def update_table(slider, branch, dataset):

	use_this_table = ''

	find_table = glob.glob('/STREAM/%s/Transition_Genes/*.tsv' % dataset)
	for table in find_table:
		if branch in table:
			use_this_table = table
			break

	if len(use_this_table) > 0:

		df = pd.read_table(use_this_table).fillna('')
		df.columns = ['gene','stat','diff','pval','qval']
		dff = df.head(n = slider)[['gene', 'pval', 'qval']] # update with your own logic

		return generate_table(dff)

if __name__ == '__main__':
	app.run_server(debug = True, processes = 5, port = 9992, host = '0.0.0.0')