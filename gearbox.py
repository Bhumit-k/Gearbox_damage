# -*- coding: utf-8 -*-
"""Untitled7.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uEHplDQ1PZiu78IimgZ4_wu_hyTf76Ln
"""

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

import os
for dirname, _, filenames in os.walk('/kaggle/input/gearbox-fault-diagnosis-elaborated-datasets/gearbox-fault-diagnosis-elaborated-datasets/stdev'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# Specific dependencies
from ipywidgets import widgets
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
import matplotlib.pyplot as plt
import math
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier

# IMPORT DATASETS
healthyDataset = pd.read_csv('/content/healthy30hz_stdev_100.csv')
brokenDataset  = pd.read_csv('/content/broken30hz_stdev_100.csv')

# CONCATENATE DATASETS INTO ONE
dataset = pd.concat([healthyDataset, brokenDataset], axis=0)
dataset.describe()

def preProcessData(df): 
    final_cols = df.columns.tolist()
    x_cols = [x for x in final_cols if x != 'failure']
    y_cols = ['failure']
    X = np.array(df[x_cols])
    Y = np.array(df[y_cols]).reshape((-1,))

    skf = StratifiedKFold(n_splits=5)
    skf.get_n_splits(X,Y);
    for i1, i2 in skf.split(X,Y):
        x_train, x_val = X[i1,:], X[i2,:]
        y_train, y_val = Y[i1], Y[i2]
        # CV is not important here, so generate only a single split
        break
    
    return x_train, y_train, x_val, y_val

def trainModels(x_train, y_train,max_iter):
    lr = LogisticRegression(max_iter=max_iter).fit(x_train, y_train)
    rf = RandomForestClassifier().fit(x_train, y_train)
    return lr, rf

def ContingencyTableForGivenThreshold(X, Y, model, thres):
    """
    Inputs:
    X: (N,D)
    Y: (N,)
    model: represents the scoring rule
    thres: scalar
    Returns the tpr, fpr for the given threshold
    """
    # compute the scores
    scores = model.predict_proba(X)[:,1] # (N,)
    # rates
    tp = np.sum((scores >= thres) & (np.array(Y)==1))
    tn = np.sum((scores < thres) & (np.array(Y)==0))
    fp = np.sum((scores >= thres) & (np.array(Y)==0))
    fn = np.sum((scores < thres) & (np.array(Y)==1))
    
    return round(tp, 3), round(fp, 3), round(tn, 3), round(fn, 3)

def CreatePlotlyInteractivePlots(x_val, y_val, lr, rf):
    # Some parameters to generate Logistic Distribution
    x_high = 10
    x_low = -10
    n_pts = 1000
    x = np.linspace(x_low, x_high, n_pts) 
    z = 1/(1 + np.exp(-(x)) )
    oneMunisZ = 1 - z
    xx = np.linspace(x_low,x_high,n_pts)
    zz= 0.5*np.ones((n_pts,))

    # Compute TPR and FPR for both models
    tpLR, fpLR, tnLR, fnLR = ContingencyTableForGivenThreshold(x_val, y_val, lr, 0.5)
    tpRF, fpRF, tnRF, fnRF = ContingencyTableForGivenThreshold(x_val, y_val, rf, 0.5)

    # Initial values to build the dashboard
    fprLR, tprLR, _ = roc_curve(y_val, lr.predict_proba(x_val)[:,1])
    fprRF, tprRF, _ = roc_curve(y_val, rf.predict_proba(x_val)[:,1])

    # Colors for dashboard plots
    cols = ['darkcyan', 'crimson']
    cols_r = ['crimson', 'darkcyan']
    
    # Sliders for thresholds for both models
    thresLR = widgets.FloatSlider(
        value=0.5,
        min=0,
        max=1,
        step = 0.01,
        description='Thres (LR):',
        continuous_update=True
    )

    thresRF = widgets.FloatSlider(
        value=0.5,
        min=0,
        max=1,
        step = 0.01,
        description='Thres (RF):',
        continuous_update=True
    )

    # Initialize the subplots object
    fig = make_subplots(rows=2,cols=2,specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "bar"}]],
                subplot_titles=("Logistic Distribution (only for Logistic Regression)","ROC Curve", "Contingency Table (LR)", "Contingency Table (RF)"),
                       vertical_spacing=0.1, horizontal_spacing=0.2)

    # Logistic Distribution plot: only useful in case of Logistic Regression
    trace11 = go.Scatter(x=x,y=z, mode='lines',
                         name = 'P(C=1)')
    trace12 = go.Scatter(x=x,y=oneMunisZ, mode='lines',
                         name = 'P(C=0)')
    trace_thres1 = go.Scatter(x=xx, y=zz, line=dict(dash='dash'),
                              name = 'Threshold')

    # ROC Curve
    trace21 = go.Scatter(x=fprLR, y=tprLR, mode='lines',
                         name ='Model horizon')
    trace_thres2 = go.Scatter(x=[fpLR/(fpLR+tnLR)], y=[tpLR/(tpLR+fnLR)],
                              mode='markers',
                              name = 'Thres (LR)', marker=dict(color="black", symbol=17, size=10)) 
    trace22 = go.Scatter(x=fprRF, y=tprRF, mode='lines',
                         name ='Model horizon')
    trace_thres21 = go.Scatter(x=[fpRF/(fpRF+tnRF)], y=[tpRF/(tpRF+fnRF)],
                              mode='markers',
                              name = 'Thres (RF)', marker=dict(color="black", symbol=4, size=10))

    # Bar plots with conditional distributions and accuracy for Logistic Regression
    trace31 = go.Bar(name='1', x=['Pred=1', 'Pred=0'],
                     y = [tpLR/(tpLR+fpLR), fnLR/(tnLR+fnLR)],
                     text = ['TP', 'FN'], textposition='inside', marker=dict(color=cols))
    trace32 = go.Bar(name='0', x=['Pred=1', 'Pred=0'],
                     y= [fpLR/(tpLR+fpLR), tnLR/(tnLR+fnLR)],
                     text = ['FP', 'TN'], textposition='inside', marker=dict(color=cols_r))
    trace33 = go.Bar(name='Acc.', x=['Acc.'],
                     y= [(tpLR+tnLR)/(tpLR+fpLR+tnLR+fnLR)],
                     text = ['Accuracy'], textposition='inside', marker=dict(color=['cornsilk']))

    # Bar plots with conditional distributions and accuracy for Random Forest
    trace41 = go.Bar(name='1', x=['Pred=1', 'Pred=0'],
                     y = [tpRF/(tpRF+fpRF), fnRF/(tnRF+fnRF)],
                     text = ['TP', 'FN'], textposition='inside', marker=dict(color=cols))
    trace42 = go.Bar(name='0', x=['Pred=1', 'Pred=0'],
                     y= [fpRF/(tpRF+fpRF), tnRF/(tnRF+fnRF)],
                     text = ['FP', 'TN'], textposition='inside', marker=dict(color=cols_r))
    trace43 = go.Bar(name='Acc.', x=['Acc.'],
                     y= [(tpRF+tnRF)/(tpRF+fpRF+tnRF+fnRF)],
                     text = ['Accuracy'], textposition='inside', marker=dict(color=['cornsilk']))


    fig.add_trace(trace11, row=1, col=1) # 0
    fig.add_trace(trace12, row=1, col=1) # 1
    fig.add_trace(trace_thres1, row=1, col=1) # 2
    fig.add_trace(trace21, row=1, col=2) # 3
    fig.add_trace(trace_thres2, row=1, col=2) # 4
    fig.add_trace(trace31, row=2, col=1) # 5
    fig.add_trace(trace32, row=2, col=1) # 6
    fig.add_trace(trace41, row=2,col=2) # 7 ##### RF Bar plot 1
    fig.add_trace(trace22, row=1, col=2) # 8
    fig.add_trace(trace_thres21, row=1, col=2) # 9
    fig.add_trace(trace33, row=2, col=1) # 10
    fig.add_trace(trace42, row=2, col=2) # 11
    fig.add_trace(trace43, row=2, col=2) # 12
    # fix this: legend is overlapping right now
    fig.update_layout(showlegend=False )
    figW = go.FigureWidget(fig)
    figW['layout']['barmode'] = 'stack'
    figW['layout']['bargap'] = 0
    figW.update_yaxes(range=[0,1], row=2, col=2);
    figW.update_yaxes(range=[0,1], row=2, col=1);
    figW.update_layout(height=570, width=900, margin=dict(l=20, r=20, t=20, b=20));
    
    return figW, thresLR, thresRF

def responseLR(change):
    n_pts = 1000
    # update the data
    zz = thresLR.value*np.ones((n_pts,))
    tp, fp, tn, fn = ContingencyTableForGivenThreshold(x_val, y_val, lr, thresLR.value)
    with figW.batch_update():
        # probab dist plot
        figW.data[2].y = zz
        # ROC Cure
        figW.data[4].x = [fp/(fp+tn)]
        figW.data[4].y = [tp/(tp+fn)]
        # Contingency table
        figW.data[5].y = [tp/(tp+fp) if tp+fp != 0 else 0, fn/(tn+fn) if tn+fn !=0 else 0]
        figW.data[6].y = [fp/(tp+fp) if tp+fp != 0 else 0, tn/(tn+fn) if tn+fn !=0 else 0]
        figW.data[10].y = [(tp+tn)/(tp+fp+tn+fn)]

def responseRF(change):
    n_pts = 1000
    # update the data
    zz = thresRF.value*np.ones((n_pts,))
    tp, fp, tn, fn = ContingencyTableForGivenThreshold(x_val, y_val, rf, thresRF.value)
    with figW.batch_update():
        # ROC Curve
        figW.data[9].x = [fp/(fp+tn)]
        figW.data[9].y = [tp/(tp+fn)]
        # Contingnecy table
        figW.data[7].y = [tp/(tp+fp) if tp+fp != 0 else 0, fn/(tn+fn) if tn+fn !=0 else 0]
        figW.data[11].y = [fp/(tp+fp) if tp+fp != 0 else 0, tn/(tn+fn) if tn+fn !=0 else 0]
        figW.data[12].y = [(tp+tn)/(tp+fp+tn+fn)]

# Run all the functions and generate outputs
x_train, y_train, x_val, y_val = preProcessData(dataset)
lr, rf = trainModels(x_train, y_train, max_iter= 1000)

# Create the interactive plot
figW, thresLR, thresRF = CreatePlotlyInteractivePlots(x_val, y_val, lr, rf)

thresLR.observe(responseLR, names="value")
thresRF.observe(responseRF, names="value")
container = widgets.HBox([thresLR, thresRF])
dashboard = widgets.VBox([container, figW])
display(dashboard)

