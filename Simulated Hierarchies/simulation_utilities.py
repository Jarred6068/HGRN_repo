# -*- coding: utf-8 -*-
"""
Created on Fri Oct 13 11:19:48 2023

@author: Bruin
"""

from utilities import Modularity, build_true_graph, resort_graph 
from utilities import sort_labels, plot_adj, plot_nodes
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sbn
import networkx as nx
import numpy as np
import pandas as pd
import torch 
import torch.nn.functional as F
import pdb
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

def compute_graph_STATs(A_all, comm_assign, layers, sp, **kwargs):
    
    mod = []
    node_deg = []
    deg_within = []
    deg_between = []
    
    indices_top, indices_mid, labels_df, sorted_true_labels_top, sorted_true_labels_middle = sort_labels(comm_assign)
    A_sorted_by_top = A_all[-1]
    #compute statistics for bottom layer
    mod.append(compute_modularity(Adj = A_sorted_by_top, 
                                  sort_labels = sorted_true_labels_top))
    node_deg.append(compute_node_degree(A_sorted_by_top))
    deg_within.append(compute_node_degree_within(A=A_sorted_by_top, 
                                                 comm_labels = sorted_true_labels_top))
    deg_between.append(compute_node_degree_between(A=A_sorted_by_top, 
                                                   comm_labels = sorted_true_labels_top))
    
    #compute middle layer statistics 
    if layers > 2:
        #A_sorted_by_middle = resort_graph(A_all[-1], indices_mid)
        
        mod.append(compute_modularity(Adj = A_sorted_by_top, 
                                      sort_labels = sorted_true_labels_middle))
        
        node_deg.append(compute_node_degree(A_sorted_by_top))
        
        deg_within.append(compute_node_degree_within(A=A_sorted_by_top, 
                                                     comm_labels = sorted_true_labels_middle))
        
        deg_between.append(compute_node_degree_between(A=A_sorted_by_top, 
                                                       comm_labels = sorted_true_labels_middle))
        print('plotting middle graph')
        print(labels_df)
        print(pd.DataFrame(sorted_true_labels_middle, columns = ['labels middle']))
        plot_nodes(A_sorted_by_top, 
                   sorted_true_labels_middle, 
                   sp+'middle_graph',
                   **kwargs)
        plot_adj(A_sorted_by_top, 
                 sp+'middle_graph_adj')
        
    print('plotting top graphs')
    plot_nodes(A_sorted_by_top, 
               sorted_true_labels_top, 
               sp+'top_graph',
               **kwargs)
    plot_adj(A_sorted_by_top,  
             sp+'top_graph_adj')
    
    
    return mod, node_deg, deg_within, deg_between









#computes the modularity of an adjacency matrix based on a set of community 
#labels
def compute_modularity(Adj, sort_labels):
    A_tensor = torch.tensor(Adj).to(torch.float64)
    labels_tensor = torch.Tensor(sort_labels).to(torch.int64)
    P = F.one_hot(labels_tensor).to(torch.float64)
    mod = Modularity(A_tensor, P)
    
    return mod.cpu().detach().numpy()






#generic function compute node degree
def compute_node_degree(A):
    deg = ((1/2)*A.sum())/A.shape[0]
    return deg
    





#this function computes the average node degree within communities given by
#a set of supplied community assignment labels
def compute_node_degree_within(A, comm_labels):
    N = A.shape[0]
    deg_list = []
    comms = np.unique(comm_labels)
    for i in range(len(np.unique(comm_labels))):
        ix = np.arange(N)[comm_labels == comms[i]]
        A_temp = A[ix,:]
        A_temp2 = A_temp[:, ix]
        deg_list.append(A_temp2.sum()/2)
        
    return np.mean(deg_list)
 


#this function computes the average node degree between communities given by
#a set of supplied community assignment labels  
def compute_node_degree_between(A, comm_labels):
    N = A.shape[0]
    deg_list = []
    comms = np.unique(comm_labels)
    for i in range(0, len(comms)):
        for j in range(0, len(comms)):
            
            if i != j:
                ix1 = np.arange(N)[comm_labels == comms[i]]
                ix2 = np.arange(N)[comm_labels == comms[j]]
                A_temp = A[ix1,:]
                A_temp2 = A_temp[:, ix2]
                deg_list.append(A_temp2.sum()/2)
            
    return np.mean(deg_list)
                





# this function uses the beth hessian to compute the number of detectable 
# communities by spectral means - method from 
# Schaub et al - Hierarchical community structure in networks
def compute_beth_hess_comms(A):
    N = A.shape[0]
    Deg = np.diag(np.matmul(A, np.ones((N, 1))).reshape(N))
    avg_degree = np.matmul(np.matmul(np.ones((N,1)).T, A), np.ones((N, 1)))/N
    eta = np.sqrt(avg_degree)
    Bethe_Hessian = (np.square(eta)-1)*np.diag(np.ones(N))+Deg - eta*A
    eigvals = np.linalg.eigh(Bethe_Hessian)[0]
    k = np.sum(eigvals<0)
    return k






def post_hoc_embedding(graph, input_X, embed, probabilities, labels, truth, 
                       is_torch = True, ns = 35, size = 10, fs=14, save = False, 
                       path = '', cm = 'plasma', **kwargs):
    layers = len(labels)
    if layers > 1:
        layer_nms = ['Middle Layer','Top Layer']
    else:
        layer_nms = 'Top Layer'
    #convert torch items     
    if is_torch:
        graph = graph.cpu().detach().numpy()
        X = embed.cpu().detach().numpy()
        IX = input_X.cpu().detach().numpy()
        probs = [i.cpu().detach().numpy() for i in probabilities]
        labels = [i.cpu().detach().numpy() for i in labels]
        
    num_nodes = input_X.shape[0]
    #plot node traced_labels
    
    
    #plots of embeddings/correlations and probabilities
    fig2, (ax3, ax4) = plt.subplots(2, 2, figsize = (15, 10))
    #heatmap of embeddings correlations
    sbn.heatmap(np.corrcoef(X), ax = ax3[0])
    ax3[0].set_title('Correlations Embeddings')
    #heatmap input data correaltions
    sbn.heatmap(np.corrcoef(IX), ax = ax3[1])
    ax3[1].set_title('Correlation matrix Input Data')
    fig_nx, ax_nx = plt.subplots(1,2,figsize=(12,10))
    
    for i in range(0, layers):
        print('plotting t-SNE and PCA for '+layer_nms[i])
        #nx graph with nodes colored by prediction
        G = nx.from_numpy_array(graph)
        templabs = np.arange(0, graph.shape[0])
        clust_labels = {list(G.nodes)[k]: templabs.tolist()[k] for k in range(len(labels[i]))}
        nx.draw_networkx(G, node_color = labels[i], 
                         labels = clust_labels,
                         font_size = fs,
                         node_size = ns,
                         cmap = cm, ax = ax_nx[i])
        ax_nx[i].set_title(layer_nms[i]+' Clusters on Graph')
        
        #tsne
        TSNE_embed=TSNE(n_components=2, 
                        learning_rate='auto',
                        init='random', 
                        perplexity=3).fit_transform(X)
        #pca
        PCs = PCA(n_components=2).fit_transform(X)
        #node labels
        nl = np.arange(TSNE_embed.shape[0])
        #figs
        fig, (ax1, ax2) = plt.subplots(2,2, figsize = (12,10))
        #tsne plot
        ax1[0].scatter(TSNE_embed[:,0], TSNE_embed[:,1], s = size, c = labels[i], cmap = cm)
        ax1[0].set_xlabel('Dimension 1')
        ax1[0].set_ylabel('Dimension 2')
        ax1[0].set_title(layer_nms[i]+' t-SNE Embeddings (Predicted)')
        #adding node labels
            
        #PCA plot
        ax1[1].scatter(PCs[:,0], PCs[:,1], s = size, c = labels[i], cmap = cm)
        ax1[1].set_xlabel('Dimension 1')
        ax1[1].set_ylabel('Dimension 2')
        ax1[1].set_title(layer_nms[i]+' PCA Embeddings (Predicted)')
        #adding traced_labels
            
        
        #TSNE and PCA plots using true cluster labels
        #tsne truth
        ax2[0].scatter(TSNE_embed[:,0], TSNE_embed[:,1], s = size, c = truth[i], cmap = cm)
        ax2[0].set_xlabel('Dimension 1')
        ax2[0].set_ylabel('Dimension 2')
        ax2[0].set_title(layer_nms[i]+' t-SNE Embeddings (Truth)')

            
        #pca truth
        ax2[1].scatter(PCs[:,0], PCs[:,1], s = size, c = truth[i], cmap = cm)
        ax2[1].set_xlabel('Dimension 1')
        ax2[1].set_ylabel('Dimension 2')
        ax2[1].set_title(layer_nms[i]+' PCA Embeddings (Truth)')
        if num_nodes < 100:
            [ax1[0].text(i, j, f'{k}', fontsize=fs, ha='right') for (i, j, k) in zip(TSNE_embed[:,0], TSNE_embed[:,1], nl)]
            [ax1[1].text(i, j, f'{k}', fontsize=fs, ha='right') for (i, j, k) in zip(PCs[:,0], PCs[:,1], nl)]
            [ax2[0].text(i, j, f'{k}', fontsize=fs, ha='right') for (i, j, k) in zip(TSNE_embed[:,0], TSNE_embed[:,1], nl)]
            [ax2[1].text(i, j, f'{k}', fontsize=fs, ha='right') for (i, j, k) in zip(PCs[:,0], PCs[:,1], nl)]
        
        sbn.heatmap(probs[i], ax = ax4[i])
        ax4[i].set_title(layer_nms[i]+' Probabilities')
        
        #save plot by layer
        if save == True:
            fig.savefig(path+layer_nms[i]+'_tSNE_PCA_Plot.png', dpi = 300)
            
    
    #save plots
    if save == True:
        fig2.savefig(path+'Embedding_and_Probs.png', dpi = 300)







































# def sort_labels(labels):
#     #pdb.set_trace()
#     true_labels = pd.DataFrame(labels, columns = ['Nodes'])
#     new_list = []
#     l = len(true_labels['Nodes'])
#     for i in np.arange(l):
#         new_list.append(list(map(int, true_labels['Nodes'][i].split('_'))))
        
#     new_list_array = np.array(new_list)
#     new_true_labels = pd.DataFrame(new_list_array[:,:2])
#     new_true_labels.columns = ['clustlabs', 'nodelabs']
#     clusts = np.unique(new_true_labels['clustlabs'])
        
#     indices_for_clusts = []
#     #extract indices for nodes belonging to each cluster
#     for i in clusts:
#         indices_for_clusts.append(new_true_labels[new_true_labels['clustlabs'] == i].index.tolist())
        

#     #pe = np.load(path+'gexp.npy').transpose()
#     #reorganize pe so that nodes are sorted according to clusters 0,1,2..etc
#     flat_list_indices = []
#     for i in clusts:
#         flat_list_indices.extend(indices_for_clusts[i])
        
        
#     #construct labels for middle layer nodes
#     if new_list_array.shape[1]>2:
#         #num_middle_nodes = new_list_array.shape[0]/len(np.unique(new_list_array[:,1]))
#         #temp = [np.repeat(i,len(np.unique(new_list_array[:,1]))).tolist() for i in np.arange(num_middle_nodes)]
#         #middle_labels = np.array([int(i[0]) for i in np.array(temp).reshape((l,1)).tolist()])
#         temp = [str(i[0])+str(i[1]) for i in new_list]
#         middle_labels = np.array(temp.copy())
#         midclusts = np.unique(temp)
#         newclusts = np.arange(len(midclusts))
#         for i in range(0, len(midclusts)):
#             middle_labels[middle_labels == midclusts[i]] = newclusts[i]
            
#         middle_labels_final = middle_labels.astype(int)
#         sorted_true_labels_middle = middle_labels_final[flat_list_indices]
#         new_true_labels['middlelabs'] = sorted_true_labels_middle
#     else:
#         sorted_true_labels_middle = []


#     #the true labels sorted by cluster
#     sort_true_labels = np.array(new_true_labels['clustlabs'][flat_list_indices])

#     return flat_list_indices, new_true_labels, sort_true_labels, sorted_true_labels_middle




















