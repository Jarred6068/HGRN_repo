# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 00:22:43 2023

@author: Bruin
"""


import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, Dataset
import time
import torch.optim as optimizers 
from utilities import Modularity, BCSS, WCSS, node_clust_eval
import matplotlib.pyplot as plt
import seaborn as sbn
from tqdm import tqdm
from utilities import resort_graph, trace_comms, node_clust_eval, gen_labels_df
from utilities import plot_loss, plot_perf, plot_adj, plot_nodes, plot_clust_heatmaps
import pdb
#------------------------------------------------------
#custom pytorch dataset
class CustomDataset(Dataset):
    def __init__(self, X):
        self.X = X

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx]

#------------------------------------------------------
#funciton which generates batches from data
def batch_data(input, batch_size, shuffle_data = True):
    """
    This function generates batches from node attribute matrix
    """
    dataset = CustomDataset(input)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    return dataloader

#-----------------------------------------------------
#function which splits training and testing data
def train_test(dataset, prop_train):
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train, test = torch.utils.data.random_split(dataset, [train_size, test_size])
    return train, test, train_size, test_size

#-----------------------------------------------------
#custom modularity loss function
class ModularityLoss(nn.Module):
    def __init__(self):
        super(ModularityLoss, self).__init__()
        
    def forward(self, all_A, all_P, resolutions):
        loss = torch.Tensor([0])
        loss_list = []
        for index, (A,P) in enumerate(zip(all_A, all_P)):
            mod = Modularity(A, P, resolutions[index])
            loss+= mod
            loss_list.append(float(mod.cpu().detach().numpy()))
        return loss, loss_list
    
#------------------------------------------------------  
class ClusterLoss(nn.Module):
    def __init__(self, weighting = ['kmeans','anova'], norm_degree=2):
        super(ClusterLoss, self).__init__()
        self.norm_deg = norm_degree
        self.weighting = weighting


    
    
    def forward(self, Lamb, Attributes, Probabilities, cluster_labels):
        
        """
        computes forward loss
        """
        #N = Attributes[0].shape[0]
        loss = torch.Tensor([0])
        loss_list = []
        #problist = [torch.eye(N)]+Probabilities
        #onehots = [torch.eye(N)]+[F.one_hot(i).type(torch.float32) for i in cluster_labels]
        for idx, (features, probs, labels) in enumerate(zip(Attributes, Probabilities, cluster_labels)):
            #compute total number of clusters
            number_of_clusters = len(torch.unique(labels))
            #within cluster sum of squares
            within_ss, centroids = WCSS(X = features,
                                        #P = problist[:(idx+2)],
                                        #S = labels,
                                        P = probs,
                                        k = number_of_clusters,
                                        norm_degree = self.norm_deg,
                                        weight_by = self.weighting)
            #between cluster sum of squares
            # between_ss = BCSS(X = Attributes,
            #                   cluster_centroids=centroids,
            #                   numclusts = number_of_clusters,
            #                   norm_degree = self.norm_deg, 
            #                   weight_by = self.weighting)
            #add loss
            loss_list.append(Lamb[idx]*float(within_ss.cpu().detach().numpy()))
            loss += Lamb[idx]*within_ss
            
            # loss_list.append(float((within_ss-between_ss).cpu().detach().numpy()))
            # loss += torch.subtract(within_ss, between_ss)

        return loss, loss_list
    
    
    
    


    
   


#------------------------------------------------------
#this function fits the HRGNgene model to data
def fit(model, X, A, optimizer='Adam', epochs = 100, update_interval=10, lr = 1e-4, 
        gamma = 1, delta = 1, lamb = 1, layer_resolutions = [1,1], normalize = True,
        comm_loss = ['Modularity', 'Clustering'], 
        true_labels = [], save_output = False, output_path = 'path/to/output', fs = 10, 
        ns = 10, turn_off_A_loss = False, verbose = True, **kwargs):
    """
    
    """
    
    #preallocate storage
    loss_history=[]
    A_loss_hist=[]
    X_loss_hist=[]
    mod_loss_hist=[]
    clust_loss_hist=[]
    perf_hist = []
    updates = []
    time_hist = []
    h_layers = len(model.comm_sizes)
    print(model)
    
    #set optimizer Adam
    optimizer = optimizers.Adam(
        model.parameters(),
        lr=lr,
        weight_decay=5e-4
    )
    
    #set loss functions
    A_recon_loss = torch.nn.BCEWithLogitsLoss(reduction = 'mean')
    #A_recon_loss = torch.nn.NLLLoss()
    X_recon_loss = torch.nn.MSELoss(reduction = 'mean')
    # if comm_loss == 'Modularity':    
    #     community_loss_fn = ModularityLoss()
    # elif comm_loss == 'Clustering':
    #     community_loss_fn = ClusterLoss(weighting='kmeans')
    
    modularity_loss_fn = ModularityLoss()
    clustering_loss_fn = ClusterLoss(weighting='kmeans')
    #pre-allocate storage space for training info
    all_out = []
    
    #------------------begin training epochs----------------------------
    for idx, epoch in enumerate(tqdm(range(epochs), desc="Fitting...", ascii=False, ncols=75)):
        #epoch printing
        start_epoch = time.time()
        if epoch % update_interval == 0:
            print('Epoch {} starts !'.format(epoch))
            print('=' * 80)
            print('=' * 80)
        total_loss = 0
        model.train()
        
        # if normalize == True:
        #     LN = nn.LayerNorm(X.shape[1])
        #     X = LN(X)
        #zero out gradient
        optimizer.zero_grad()
        #batch = data.transpose(0,1)
        #compute forward output
        X_hat, A_hat, X_all, A_all, P_all, S = model.forward(X, A)
        S_sub, S_relab, S_all = trace_comms([i.cpu().clone() for i in S], model.comm_sizes)
        
        #update all output list
        all_out.append([X_hat, A_hat, X_all, A_all, P_all, S_relab, S_all, [len(np.unique(i.cpu())) for i in S_all]])
        
        
        
        #compute reconstruction losses for graph and attributes
        X_loss = X_recon_loss(X_hat, X)
        A_loss = A_recon_loss(A_hat, A)
        #compute community detection loss
        Mod_loss, Modloss_values = modularity_loss_fn(A_all, P_all, layer_resolutions)
        Clust_loss, Clustloss_values = clustering_loss_fn(lamb, X_all, P_all, S)
        
        #compute community detection loss
        # if comm_loss == 'Modularity':    
        #     community_loss, comloss_values = community_loss_fn(A_all, P_all, layer_resolutions)
        #     #compute total loss function
        #     if(turn_off_A_loss == True):
        #         loss = 0*A_loss+gamma*X_loss-delta*community_loss
        #     else:
        #         loss = A_loss+gamma*X_loss-delta*community_loss
        # elif comm_loss == 'Clustering':
        #     community_loss, comloss_values = community_loss_fn(X_all, P_all, S_sub)
        #     #compute total loss function
        #     if(turn_off_A_loss == True):
        #         loss = 0*A_loss+gamma*X_loss+delta*community_loss
        #     else:
        #         loss = A_loss+gamma*X_loss+delta*community_loss
        
        #option to turn of adjacency matrix loss - this is for testing only
        if(turn_off_A_loss == True):
            loss = 0*A_loss+gamma*X_loss+Clust_loss-delta*Mod_loss
        else:
            loss = A_loss+gamma*X_loss+Clust_loss-delta*Mod_loss
        

        #compute backward pass
        loss.backward()
        #update gradients
        optimizer.step()
        #update total loss function
        total_loss += loss.cpu().item()
        
        #store loss component information
        loss_history.append(total_loss)
        A_loss_hist.append(float(A_loss.cpu().detach().numpy()))
        X_loss_hist.append(float(X_loss.cpu().detach().numpy()))
        mod_loss_hist.append(Modloss_values)
        clust_loss_hist.append(Clustloss_values)
        #evaluating performance homogenity, completeness and NMI
        perf_layers = []
        lnm = ['top']+['middle_'+str(i) for i in np.arange(h_layers-1)[::-1]]
        if h_layers <3:
            for i in range(0, len(S_all)):   
                preds = S_relab[::-1][-2:][i].cpu().detach().numpy()
                eval_metrics = node_clust_eval(true_labels=true_labels[::-1][i],
                                               pred_labels=preds, 
                                               verbose=False)
                perf_layers.append(eval_metrics.tolist())
            perf_hist.append(perf_layers)
        
        
        #evaluate epoch
        if (epoch+1) % update_interval == 0:
            
            #store update interval
            updates.append(epoch+1)
            model.eval()
            #model forward
            X_pred, A_pred, X_list, A_list, P_list, S_pred = model.forward(X, A)
            #print update of performance metrics
            if h_layers < 3:
                for i in range(0, h_layers):
                    print('-' * 36 + '{} layer'.format(lnm[i]) + '-' * 36)
                    print('\nHomogeneity = {:.4f}, \nCompleteness = {:.4f}, \nNMI = {:.4f}'.format(
                        perf_hist[-1][i][0], perf_hist[-1][i][1], perf_hist[-1][i][2]))
                    print('-' * 80)
            
            
            #loss printing
            #------------------------------
            print('\nEpoch {} \nTotal Loss = {:.4f}'.format(
                epoch+1, total_loss
                ))
            

            print('\nModularity = {}, \nClustering = {}, \nX Recontrstuction = {:.4f}, \nA Recontructions = {:.4f}'.format(
                np.round(mod_loss_hist[-1],4),
                np.round(clust_loss_hist[-1],4),
                X_loss_hist[-1], 
                A_loss_hist[-1]))
           
            
            
            #------------------------------
            #plotting training curves
            if ((epoch+1) >= 10):
                #loss plot
                print('plotting loss curve...')
                plot_loss(epoch = epoch, 
                          loss_history = loss_history, 
                          recon_A_loss_hist = A_loss_hist, 
                          recon_X_loss_hist = X_loss_hist, 
                          mod_loss_hist = mod_loss_hist,
                          clust_loss_hist = clust_loss_hist,
                          path=output_path, 
                          save = save_output)
                if verbose == True:
                    #plotting graphs in networkx 
                    print('plotting nx graphs...')
                    plot_nodes(A = (A-torch.eye(A.shape[0])).cpu().detach().numpy(), 
                               labels=S_relab[-1], 
                               path = output_path+'Top_Clusters_result_'+str(epoch+1),
                               node_size=ns, 
                               font_size=fs,
                               save = save_output,
                               add_labels = True)
                    if h_layers == 2:
                        plot_nodes(A = (A-torch.eye(A.shape[0])).cpu().detach().numpy(), 
                                   labels=S_relab[0], 
                                   add_labels = True,
                                   node_size=ns,
                                   font_size=fs,
                                   save=save_output,
                                   path = output_path+'midde_Clusters_result_'+str(epoch+1))
                    
                if verbose == True: #plotting heatmaps: 
                    print('plotting heatmaps...')
                    plot_clust_heatmaps(A = A, 
                                        A_pred = A_pred, 
                                        true_labels = true_labels, 
                                        pred_labels = S_relab, 
                                        layers = h_layers+1, 
                                        epoch = epoch+1, 
                                        save_plot = save_output, 
                                        sp = output_path)
                
                
                
            if len(perf_hist)>1:
                print('plotting performance curves')
                #performance plot
                plot_perf(update_time = updates[-1], 
                          performance_hist = perf_hist, 
                          epoch = epoch, 
                          path= output_path, 
                          save = save_output)
                
            
                
                
            
            print(".... Average epoch time = %.2f seconds ---" % (np.mean(time_hist)))
        time_hist.append(time.time() - start_epoch)
            
    #return 
    X_final, A_final, X_all_final, A_all_final, P_all_final, S_final = model.forward(X, A)
    return all_out, X_final, A_final, X_all_final, A_all_final, P_all_final, S_final, mod_loss_hist, loss_history, clust_loss_hist, A_loss_hist, X_loss_hist, perf_hist