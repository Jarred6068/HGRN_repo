# -*- coding: utf-8 -*-
"""
Created on Sat Aug 26 11:50:12 2023

@author: Bruin
"""
import numpy as np
import pandas as pd
import networkx as nx
import seaborn as sbn
import matplotlib.pyplot as plt
from simulation_software.HGRN_hierarchicalgraph import hierachical_graph 
from simulation_software.HGRN_hierarchicalgraph import generate_pseudo_expression, generate_pseudo_expression_weighted
from simulation_software.HGRN_hierarchicalgraph import same_cluster
from simulation_software.simulation_utilities import plot_diGraph
from model.utilities import pickle_data, sort_labels
from random import randint as rd   






def simulate_graph(args): 
    
    
    if args.set_seed:
        if args.seed_number:
            rd.seed(args.seed_number)
        else:
            rd.seed(rd(100, 1000))
        
        
    
    #seed(args.seed_number)
    nodes_by_layer = []
    edges_by_layer = []
    if args.connect == 'full':
        #randomly generate first layer of hierarchy
        h1_graph = nx.watts_strogatz_graph(args.top_layer_nodes, 
                                           args.top_layer_nodes, 
                                           args.subgraph_prob)
        #h1_graph = nx.erdos_renyi_graph(args.top_layer_nodes, args.toplayer_connect_prob, directed=True)
        h1_graph = nx.DiGraph([(u,v) for (u,v) in h1_graph.edges() if u!=v])

        #draw directed graph
        fig, ax = plt.subplots(figsize = (14,10))
        topfig = plot_diGraph(fig, ax, h1_graph, return_fig=True)
        topfig.savefig(args.savepath+'top_layer_graph.pdf')
        topfig.savefig(args.savepath+'top_layer_graph.png', dpi = 500)
        
        #sort toplayer
        ts_h1_graph = list(nx.topological_sort(h1_graph))
        adj_h1_graph = nx.adjacency_matrix(h1_graph, ts_h1_graph).todense()
        h1_in_degree = [i[1] for i in h1_graph.in_degree()]
        h1_out_degree = [i[1] for i in h1_graph.in_degree()]
        
    if args.connect == 'disc':
    
        h1_graph =  np.zeros((args.top_layer_nodes,args.top_layer_nodes))
        h1_graph = nx.from_numpy_array(h1_graph)
        
        #draw top graph
        #draw directed graph
        fig, ax = plt.subplots(figsize = (14,10))
        topfig = plot_diGraph(fig, ax, h1_graph, return_fig=True)
        topfig.savefig(args.savepath+'top_layer_graph.pdf')
        topfig.savefig(args.savepath+'top_layer_graph.png', dpi = 500)
        
        #sort toplayer
        ts_h1_graph = list(h1_graph.nodes())
        adj_h1_graph = nx.adjacency_matrix(h1_graph, ts_h1_graph).todense()
        h1_in_degree = 0
        h1_out_degree = 0
        
        
    print('-'*60)
    print("Number of edges: {} \nNumber of nodes: {} \n Mean In degree: {} \n Mean Out degree: {}".format(
        h1_graph.number_of_edges(), h1_graph.number_of_nodes(),
        np.mean(h1_in_degree), np.mean(h1_out_degree)))
    print('-'*60)
    nodes_by_layer.append(h1_graph.number_of_nodes())
    edges_by_layer.append(h1_graph.number_of_edges())
    
    h2_graph, subgraphs2 = hierachical_graph(top_graph=h1_graph, 
                                 subgraph_node_number=args.nodes_per_super2, 
                                 subgraph_type =args.subgraph_type, 
                                 sub_graph_prob=args.subgraph_prob[0], 
                                 connection_prob_within=args.connect_prob_middle[0],
                                 connection_prob_between = args.connect_prob_middle[1],
                                 degree=args.node_degree_middle,
                                 weight_w = args.within_edgeweights,
                                 weight_b = args.between_edgeweights,
                                 as_weighted = args.use_weighted_graph,
                                 force_connections= args.force_connect)
        
    #sort middle layer
    ts_h2_graph = list(nx.topological_sort(h2_graph))
    adj_h2_graph = nx.adjacency_matrix(h2_graph, ts_h2_graph).todense()
    
    
    
    #print toplayer attributes
    print('-'*60)
    print("Number of edges: {} \nNumber of nodes: {} \nIn degree: {} \nOut degree: {}".format(
        h2_graph.number_of_edges(), h2_graph.number_of_nodes(),
        np.mean([i[1] for i in h2_graph.in_degree()]), 
        np.mean([i[1] for i in h2_graph.out_degree()])))
    print('-'*60)
    nodes_by_layer.append(h2_graph.number_of_nodes())
    edges_by_layer.append(h2_graph.number_of_edges())
    if args.layers == 2:
        #draw top layer
        fig, ax = plt.subplots(figsize = (14,10))
        midfig = plot_diGraph(fig, ax, h2_graph, return_fig=True, draw_edge_weights = True)
        midfig.savefig(args.savepath+'bottom_layer_graph.pdf')
        midfig.savefig(args.savepath+'bottom_layer_graph.png', dpi = 500)
    else:
        #draw top layer
        fig, ax = plt.subplots(figsize = (14,10))
        midfig = plot_diGraph(fig, ax, h2_graph, return_fig=True, draw_edge_weights = False)
        midfig.savefig(args.savepath+'middle_layer_graph.pdf')
        midfig.savefig(args.savepath+'middle_layer_graph.png', dpi = 500)
        
        h3_graph, subgraphs3 = hierachical_graph(top_graph=h2_graph, 
                                     subgraph_node_number=args.nodes_per_super3, 
                                     subgraph_type =args.subgraph_type, 
                                     sub_graph_prob=args.subgraph_prob[1], 
                                     connection_prob_within=args.connect_prob_bottom[0],
                                     connection_prob_between = args.connect_prob_bottom[1],
                                     degree=args.node_degree_bottom,
                                     weight_w = args.within_edgeweights,
                                     weight_b = args.between_edgeweights,
                                     as_weighted = args.use_weighted_graph,
                                     force_connections= args.force_connect)
        
        
        ts_h3_graph = list(nx.topological_sort(h3_graph))
        adj_h3_graph = nx.adjacency_matrix(h3_graph, ts_h3_graph).todense()
        #draw middle layer
        fig, ax = plt.subplots(figsize = (14,10))
        botfig = plot_diGraph(fig, ax, h3_graph, return_fig=True)
        botfig.savefig(args.savepath+'bottom_layer_graph.pdf')
        botfig.savefig(args.savepath+'bottom_layer_graph.png', dpi = 500)
        #print toplayer attributes
        print('-'*60)
        print("Number of edges: {} \nNumber of nodes: {} \nIn degree: {} \nOut degree: {}".format(
            h3_graph.number_of_edges(), h3_graph.number_of_nodes(),
            np.mean([i[1] for i in h3_graph.in_degree()]), 
            np.mean([i[1] for i in h3_graph.out_degree()])))
        print('-'*60)
        
        
        nodes_by_layer.append(h3_graph.number_of_nodes())
        edges_by_layer.append(h3_graph.number_of_edges())

    h1_undi = h1_graph.to_undirected()
    h2_undi = h2_graph.to_undirected()
    h1_undi_adj = nx.to_numpy_array(h1_undi)
    h2_undi_adj = nx.to_numpy_array(h2_undi)
    if args.layers == 2:
        
        ts_full = ts_h2_graph
        adj_full = nx.adjacency_matrix(h2_graph, ts_full).todense()
        print(len(ts_full), adj_full.shape)
    
    else:

        h3_undi = h3_graph.to_undirected()
        h3_undi_adj = nx.to_numpy_array(h3_undi)
        ts_full = list(nx.topological_sort(h3_graph))
        adj_full = nx.adjacency_matrix(h3_graph, ts_full).todense()
        
    print(len(ts_full), adj_full.shape)
    
    print('Generating pseudoexpression...')
    if args.use_weighted_graph:
        pe, ori_nodes = generate_pseudo_expression_weighted(topological_order=ts_full, 
                                                   adjacency_matrix=adj_full, 
                                                   number_of_invididuals=args.sample_size,
                                                   free_mean=0,
                                                   std=args.SD,
                                                   common_distribution=args.common_dist)
    else:
        pe, ori_nodes = generate_pseudo_expression(topological_order=ts_full, 
                                                   adjacency_matrix=adj_full, 
                                                   number_of_invididuals=args.sample_size,
                                                   free_mean=0,
                                                   std=args.SD,
                                                   common_distribution=args.common_dist)
    
    print('data dimension = {}'.format(pe.shape))
    #pdb.set_trace()
    #save as .npz
    if args.layers == 2:
        np.savez(args.savepath, layer1 = h1_undi, 
                 adj_layer1 = h1_undi_adj,
                 layer2 = h2_undi, 
                 adj_layer2 = h2_undi_adj,
                 gen_express= pe,
                 labels = ts_full)
        
        pickle_data([h1_graph, [h2_graph, subgraphs2]], 
                    filepath = args.savepath,
                    filename = 'directed_graphs')
        
        adj_all = [h1_undi_adj, h2_undi_adj]
        nx_all = [ts_h1_graph, ts_full]
    else:
        np.savez(args.savepath+'.npz', layer1 = h1_undi, 
                 adj_layer1 = h1_undi_adj,
                 layer2 = h2_undi, 
                 adj_layer2 = h2_undi_adj,
                 layer3 = h3_undi, 
                 adj_layer3= h3_undi_adj, 
                 gen_express= pe,
                 labels = ts_full)
        
        pickle_data([h1_graph, [h2_graph, subgraphs2], [h3_graph, subgraphs3]], 
                    filepath = args.savepath,
                    filename = 'directed_graphs')
        
        adj_all = [h1_undi_adj, h2_undi_adj, h3_undi_adj]
        nx_all = [ts_h1_graph, ts_h2_graph, ts_full]
        
    gene_list, sample_list = ts_full, range(args.sample_size)
    gexp = pd.DataFrame(data=np.transpose(pe), index=sample_list, columns=gene_list)
    print(gexp.shape)
    gexp.to_csv(args.savepath+'_gexp.csv')
    gexp_numpy = gexp.to_numpy()
    np.save(args.savepath+'_gexp.npy', gexp_numpy)
    gexp.head()
    
    
    indices_top, indices_mid, true_labels, sorted_top, sorted_middle = sort_labels(gene_list)
    
    fig, ax = plt.subplots(1,2, figsize = (16, 10))
    if args.layers > 2:
        sbn.heatmap(h3_undi_adj, ax = ax[1])
        sbn.heatmap(np.corrcoef(pe[indices_mid, :]), ax = ax[0])
    else:
        sbn.heatmap(h2_undi_adj, ax = ax[1])
        sbn.heatmap(np.corrcoef(pe[indices_top, :]), ax = ax[0])
    
    fig.savefig(args.savepath+'heatmaps.pdf')
    fig.savefig(args.savepath+'heatmaps.png', dpi = 500)
    
    plt.close('all')
    
    return pe, gexp, nodes_by_layer, edges_by_layer, nx_all, adj_all, args.savepath, ts_full, ori_nodes