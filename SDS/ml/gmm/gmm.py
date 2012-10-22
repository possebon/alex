#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This code is based on https://github.com/scikit-learn/scikit-learn/blob/master/sklearn/mixture/gmm.py code
# which is distributed under the new BSD license.

import numpy as np
import cPickle as pickle

from sklearn.utils.extmath import logsumexp

EPS = np.finfo(float).eps


class GMM:
    """This is a GMM model of the input data.
    It is memory efficient so that it can process very large input array like objects.

    The mixtures are incrementally added by splitting the heaviest component in two components and
    perturbation of the original mean.

    """

    def __init__(self, n_features=1, n_components=1, thresh=1e-3, min_covar=1e-3, n_iter=1):
        self.n_features = n_features
        self.n_components = n_components
        self.thresh = thresh
        self.min_covar = min_covar
        self.n_iter = n_iter

        self.weights = np.ones(self.n_components) / self.n_components
        self.means = np.zeros((self.n_components, self.n_features))
        self.covars = np.ones((self.n_components, self.n_features))

    def __str__(self):
        s = []
        s.append("W: %s" % str(self.weights))
        s.append("M: %s" % str(self.means))
        s.append("C: %s" % str(self.covars))

        return '\n'.join(s)

    def log_multivariate_normal_density_diag(self, x, means=0.0, covars=1.0):
        """Compute Gaussian log-density at X for a diagonal model"""
        s, n_dim = x.shape

        lpr = - 0.5 * (n_dim * np.log(2 * np.pi) + np.sum(
            np.log(covars), 1)) - 0.5 * np.sum(((x - means) ** 2 / covars), 1)

#    print "m", means
#    print "c", covars
#    print "lm", - 0.5* np.sum(((x - means) ** 2) / covars)

        return lpr

    def expectation(self, x):
        """ Evaluate one example
        """
        lpr = np.log(self.weights) + self.log_multivariate_normal_density_diag(
            x, self.means, self.covars)

#    print "lpr", lpr
        log_prob = logsumexp(lpr)
        responsibilities = np.exp(lpr - log_prob)

        return log_prob, responsibilities

    def score(self, x):
        """Get the log prob of the x variable being generated by the mixture."""
        x = x.reshape((1, len(x)))

        lpr = np.log(self.weights) + self.log_multivariate_normal_density_diag(
            x, self.means, self.covars)
        log_prob = logsumexp(lpr)

        return log_prob

    def mixup(self, n_new_mixies):
        """Add n new mixies to the mixture."""

        for n in range(n_new_mixies):
            # the heaviest compnent
            c_to_split = np.argmax(self.weights)
#      print "weights", self.weights
#      print "cts", c_to_split

            c_weights = self.weights[c_to_split]
            c_means = self.means[c_to_split]
            c_covars = self.covars[c_to_split]

#      print c_weights
#      print c_means
#      print c_covars

            # add the first component
            new_weights = np.append(self.weights, c_weights / 2)
            new_means = np.append(self.means, np.random.multivariate_normal(
                c_means, np.diag(c_covars * (0.2 ** 2)))[np.newaxis, :], 0)
            new_covars = np.append(self.covars, c_covars[np.newaxis, :], 0)

            # add the second component
            new_weights = np.append(new_weights, c_weights / 2)
            new_means = np.append(new_means, np.random.multivariate_normal(
                c_means, np.diag(c_covars * (0.2 ** 2)))[np.newaxis, :], 0)
            new_covars = np.append(new_covars, c_covars[np.newaxis, :], 0)

            new_weights = np.delete(new_weights, c_to_split)
            new_means = np.delete(new_means, c_to_split, 0)
            new_covars = np.delete(new_covars, c_to_split, 0)

            self.weights, self.means, self.covars = new_weights, new_means, new_covars

            self.n_components += 1

    def fit(self, X):
        # init the algorithm

        self.log_probs = []
        for i in range(self.n_iter):
            log_prob = 0
            n = 0

            acc_weights = np.zeros(self.n_components)
            acc_means = np.zeros((self.n_components, self.n_features))
            acc_covars = np.zeros((self.n_components, self.n_features))

            for x in X:
                x_m = x.reshape((1, len(x)))
                #expectation
                log_prob_x, responsibilities = self.expectation(x_m)

#        print x
#        print "r", responsibilities

                # maximisation
                acc_weights += responsibilities

                # make a column matrix from it
                responsibilities = responsibilities[:, np.newaxis]

#        print responsibilities

                acc_means += np.dot(responsibilities, x_m)

#        print (x_m - self.means)**2

#        print "r", responsibilities.T
#        print "d", x_m - self.means
#        print "d**2", (x_m - self.means)**2
#        print "ac", responsibilities * (x_m - self.means)**2

                acc_covars += responsibilities * (x_m - self.means) ** 2

                log_prob += log_prob_x
                n += 1

#        print "LP", log_prob_x
#        if n > 100000:
#          break

            self.log_probs.append(log_prob / n)

#      print "Iter:", i, "Log prob of data: ", log_prob/n

            if i > 2 and abs(self.log_probs[-1] - self.log_probs[-2]) < self.thresh:
                break

            new_weights = (acc_weights + EPS) / (n + self.n_components * EPS)
            new_means = (acc_means + EPS) / (
                acc_weights[:, np.newaxis] + self.n_components * EPS)
            new_covars = (acc_covars + EPS) / (acc_weights[:, np.newaxis]
                                               + self.n_components * EPS) + self.min_covar

            self.weights, self.means, self.covars = new_weights, new_means, new_covars

    def save_model(self, file_name):
        """Save the GMM model as a pickle."""
        f = open(file_name, 'w+')
        d = [self.n_features,
             self.n_components,
             self.thresh,
             self.min_covar,
             self.n_iter,
             self.weights,
             self.means,
             self.covars,
             ]

        pickle.dump(d, f)
        f.close()

    def load_model(self, file_name):
        """Load the model from a pickle.load"""
        f = open(file_name, 'r')
        d = pickle.load(f)
        self.n_features, self.n_components, self.thresh, self.min_covar, self.n_iter, self.weights, self.means, self.covars = d
        f.close()
