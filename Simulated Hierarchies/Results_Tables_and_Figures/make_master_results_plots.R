
library(ggubr)
tab = read.csv('C:/Users/Bruin/Documents/GitHub/HGRN_repo/Simulated Hierarchies/MASTER_results.csv')

ggplot(data = tab, aes(x = Network_type, y = Modularity_top, fill = as.factor(Resolution_top)))+
  geom_boxplot()



subtab = subset(tab, Resolution_top == 1)
ggplot(data = subtab, aes(x = True_mod_top, y = Modularity_top))+geom_point()


tab$Resolution_top = as.factor(tab$Resolution_top)
tab$Resolution_middle = as.factor(tab$Resolution_middle)
ggplot(data = tab, aes(x = Network_type, y = Top_homogeneity, fill = Resolution_top))+
  geom_boxplot()+
  facet_wrap(~Gamma)

ggplot(data = tab, aes(x = Network_type, y = Top_homogeneity, fill = Resolution_middle))+
  geom_boxplot()+
  facet_wrap(~Gamma)


longform = cbind.data.frame(metric = as.factor(c(rep('homogeneity', dim(tab)[1]),
                              rep('completeness', dim(tab)[1]),
                              rep('NMI', dim(tab)[1]))),
                            network = as.factor(rep(tab$Network_type, 3)),
                            input_graph = as.factor(rep(tab$input_graph, 3)),
                            gamma = as.factor(rep(tab$Gamma, 3)),
                            resolution_top = as.factor(rep(tab$Resolution_top, 3)),
                            resolution_middle = as.factor(rep(tab$Resolution_middle, 3)),
                            Top.stats = c(tab$Top_homogeneity, tab$Top_completeness, tab$Top_NMI),
                            Mid.stats = c(tab$Middle_homogeneity, tab$Middle_Completeness, tab$Middle_NMI),
                            Louvain.top = c(tab$Louvain_homogenity_top, 
                                            tab$Louvain_completeness_top, 
                                            tab$Louvain_NMI_top),
                            Louvain.middle = c(tab$Louvain_homogenity_middle, 
                                               tab$Louvain_completeness_middle,
                                               tab$Louvain_NMI_middle))

# ggplot(data = longform, aes(x = Top.stats, y = Mid.stats, color = metric))+
#   geom_point()+
#   geom_smooth(method = 'lm')+
#   xlab('Peformance Top Layer')+
#   ylab('Performance Middle Layer')+
#   facet_wrap(~input_graph)+
#   theme_classic2()+
#   theme(legend.position = 'top')
#   
#   
# ggplot(data = longform, aes(x = Top.stats, y = Mid.stats, color = metric))+
#   geom_point()+
#   geom_smooth(method = 'lm')+
#   xlab('Peformance Top Layer')+
#   ylab('Performance Middle Layer')+
#   facet_wrap(~network)+
#   theme_classic2()+
#   theme(legend.position = 'top')


#plotted over gamma parameter
ggplot(data = longform, aes(x = gamma, y = Top.stats, fill = metric))+
  geom_boxplot()+
  xlab('Weight Applied to Reconstruction Loss')+
  ylab('Performance Top Layer')+
  facet_wrap(~network)+
  theme_classic2()+
  theme(legend.position = 'top')


ggplot(data = longform, aes(x = gamma, y = Mid.stats, fill = metric))+
  geom_boxplot()+
  xlab('Weight Applied to Reconstruction Loss')+
  ylab('Performance Middle Layer')+
  facet_wrap(~network)+
  theme_classic2()+
  theme(legend.position = 'top')

#plotted over resolution parameter
ggplot(data = longform, aes(x = resolution_top, y = Top.stats, fill = metric))+
  geom_boxplot()+
  xlab('Resolution Value')+
  ylab('Performance Top Layer')+
  facet_wrap(~network)+
  theme_classic2()+
  theme(legend.position = 'top')


ggplot(data = longform, aes(x = resolution_middle, y = Mid.stats, fill = metric))+
  geom_boxplot()+
  xlab('Resolution Value')+
  ylab('Performance Middle Layer')+
  facet_wrap(~network)+
  theme_classic2()+
  theme(legend.position = 'top')


#Louvain Perfomance
ggplot(data = longform, aes(x = input_graph, y = Louvain.top, fill = metric))+
  geom_boxplot()+
  xlab('Input Graph')+
  ylab('Louvain Performance Top Layer')+
  facet_wrap(~network)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))


ggplot(data = longform, aes(x = input_graph, y = Louvain.middle, fill = metric))+
  geom_boxplot()+
  xlab('Resolution Value')+
  ylab('Louvain Performance Middle Layer')+
  facet_wrap(~network)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))

longform2 = cbind.data.frame(method = as.factor(c(rep('HCD', dim(longform)[1]), 
                                        rep('Louvain', dim(longform)[1]))),
                             metric = as.factor(rep(c(rep('homogeneity', dim(tab)[1]),
                                         rep('completeness', dim(tab)[1]),
                                         rep('NMI', dim(tab)[1])), 2)),
                  network = as.factor(rep(tab$Network_type, 6)),
                  input_graph = as.factor(rep(tab$input_graph, 6)),
                  gamma = as.factor(rep(tab$Gamma, 6)),
                  resolution_top = as.factor(rep(tab$Resolution_top, 6)),
                  resolution_middle = as.factor(rep(tab$Resolution_middle, 6)),
                  stats.top = c(longform$Top.stats, longform$Louvain.top),
                  stats.mid = c(longform$Mid.stats, longform$Louvain.top))


#comparing Louvain and HCD:

#Top level comparison
#smallworld network
lf1.1 = subset(longform2, network == 'small world')
ggplot(data = lf1.1, aes(x = method, y = stats.top, 
                             fill = metric))+
  geom_boxplot()+
  xlab('Method')+
  ylab('Top Layer Performance')+
  facet_wrap(~input_graph)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))

#scale free
lf1.2 = subset(longform2, network == 'scale free')
ggplot(data = lf1.2, aes(x = method, y = stats.top, 
                             fill = metric))+
  geom_boxplot()+
  xlab('Method')+
  ylab('Top Layer Performance')+
  facet_wrap(~input_graph)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))

#random graph
lf1.3 = subset(longform2, network == 'random graph')
ggplot(data = lf1.3, aes(x = method, y = stats.top, 
                             fill = metric))+
  geom_boxplot()+
  xlab('Method')+
  ylab('Top Layer Performance')+
  facet_wrap(~input_graph)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))



#comparing Louvain and HCD:
#comparing on middle level
#smallworld network
lf1.1 = subset(longform2, network == 'small world')
ggplot(data = lf1.1, aes(x = method, y = stats.mid, 
                         fill = metric))+
  geom_boxplot()+
  xlab('Method')+
  ylab('Top Layer Performance')+
  facet_wrap(~input_graph)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))

#scale free
lf1.2 = subset(longform2, network == 'scale free')
ggplot(data = lf1.2, aes(x = method, y = stats.mid, 
                         fill = metric))+
  geom_boxplot()+
  xlab('Method')+
  ylab('Top Layer Performance')+
  facet_wrap(~input_graph)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))

#random graph
lf1.3 = subset(longform2, network == 'random graph')
ggplot(data = lf1.3, aes(x = method, y = stats.mid, 
                         fill = metric))+
  geom_boxplot()+
  xlab('Method')+
  ylab('Top Layer Performance')+
  facet_wrap(~input_graph)+
  theme_classic2()+
  theme(legend.position = 'top', axis.text.x = element_text(angle = 90))


















longform3 = cbind.data.frame(method = as.factor(c(rep('HCD_middle', dim(tab)[1]),
                                                  rep('HCD_top', dim(tab)[1]),
                                                  rep('Louvain', dim(tab)[1]))),
                             predicted = c(tab$Comms_predicted_middle, 
                                           tab$Comms_predicted_top,
                                           tab$Louvain_predicted))
ggplot(data = longform3, aes(x = method, y = predicted))+geom_boxplot()


summary(subset(tab, input_graph == 'A_corr_no_cutoff')$Top_homogeneity)
summary(subset(tab, input_graph == 'A_corr_no_cutoff')$Top_completeness)
summary(subset(tab, input_graph == 'A_corr_no_cutoff')$Top_NMI)