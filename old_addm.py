#!/usr/bin/python

"""
old_addm.py
Author: Gabriela Tavares, gtavares@caltech.edu

Old implementation of the attentional drift-diffusion model (aDDM). This
algorithm uses reaction time histograms conditioned on choice from both data
and simulations to estimate each model's likelihood. Here we perforrm a test to
check the validity of this algorithm. Artificil data is generated using
specific parameters for the model. These parameters are then recovered through
a maximum likelihood estimation procedure, using a grid search over the 3 free
parameters of the model.
"""

import argparse
import numpy as np

from multiprocessing import Pool

from addm import aDDMTrial
from util import load_data_from_csv, get_empirical_distributions


def wrap_addm_get_model_likelihood(args):
    """
    Wrapper for aDDM.get_model_likelihood(), intended for parallel computation
    using a threadpool.
    Args:
      args: a tuple where the first item is an aDDM object, and the remaining
          item are the same arguments required by aDDM.get_model_likelihood().
    Returns:
      The output of aDDM.get_model_likelihood().
    """
    model = args[0]
    return model.get_model_likelihood(*args[1:])


class aDDM:
    """
    Implementation of the attentional drift-diffusion model (aDDM), as
    described by Krajbich et al. (2010).
    """
    def __init__(self, d, sigma, theta, barrier=1):
        """
        Args:
          d: float, parameter of the model which controls the speed of
              integration of the signal.
          sigma: float, parameter of the model, standard deviation for the
              normal distribution.
          theta: float between 0 and 1, parameter of the model which controls
              the attentional bias.
          barrier: positive number, magnitude of the signal thresholds.
        """
        self.d = d
        self.sigma = sigma
        self.theta = theta
        self.barrier = barrier
        self.params = (d, sigma, theta)


    def simulate_trial(self, valueLeft, valueRight, fixationData, timeStep=10,
                       numFixDists=3, visualDelay=0, motorDelay=0):
        """
        Generates an aDDM trial given the item values and some empirical
        fixation data, which are used to generate the simulated fixations.
        Args:
          valueLeft: value of the left item.
          valueRight: value of the right item.
          fixationData: a FixationData object.
          timeStep: integer, value in miliseconds to be used for binning the
              time axis.
          numFixDists: integer, number of fixation types to use in the fixation
              distributions. For instance, if numFixDists equals 3, then 3
              separate fixation types will be used, corresponding to the 1st,
              2nd and other (3rd and up) fixations in each trial.
          visualDelay: delay to be discounted from the beginning of all
              fixations, in miliseconds.
          motorDelay: delay to be discounted from the last fixation only, in
              miliseconds.
        Returns:
          An aDDMTrial object resulting from the simulation.
        """
        RDV = 0
        RT = 0
        trialTime = 0
        choice = 0
        fixItem = list()
        fixTime = list()
        fixRDV = list()

        # Sample and iterate over the latency for this trial.
        trialAborted = False
        while True:
            latency = np.random.choice(fixationData.latencies)
            for t in xrange(int(latency // timeStep)):
                # Sample the change in RDV from the distribution.
                RDV += np.random.normal(0, self.sigma)
                # If the RDV hit one of the barriers, we abort the trial,
                # since a trial must end on an item fixation.
                if RDV >= self.barrier or RDV <= -self.barrier:
                    trialAborted = True
                    break

            if trialAborted:
                RDV = 0
                trialAborted = False
                continue
            else:
                # Add latency to this trial's data.
                fixRDV.append(RDV)
                fixItem.append(0)
                fixTime.append(latency - (latency % timeStep))
                trialTime += latency - (latency % timeStep)
                break

        fixUnfixValueDiffs = {1: valueLeft - valueRight,
                              2: valueRight - valueLeft}
        
        probLeftRight = np.array([fixationData.probFixLeftFirst,
                                  1 - fixationData.probFixLeftFirst])
        currFixItem = np.random.choice([1, 2], p=probLeftRight)
        valueDiff = fixUnfixValueDiffs[currFixItem]
        currFixTime = np.random.choice(fixationData.fixations[1][valueDiff])

        decisionReached = False
        fixNumber = 2
        while True:
            for t in xrange(int(currFixTime // timeStep)):
                if RDV >= self.barrier or RDV <= -self.barrier:
                    if RDV >= self.barrier:
                        choice = -1
                    elif RDV <= -self.barrier:
                        choice = 1
                    fixRDV.append(RDV)
                    fixItem.append(currFixItem)
                    fixTime.append(((t + 1) * timeStep) + motorDelay)
                    trialTime += ((t + 1) * timeStep) + motorDelay
                    RT = trialTime
                    decisionReached = True
                    break

                epsilon = np.random.normal(0, self.sigma)
                if currFixItem == 1:
                    RDV += (self.d *
                            (valueLeft - (self.theta * valueRight))) + epsilon
                elif currFixItem == 2:
                    RDV += (self.d *
                            (-valueRight + (self.theta * valueLeft))) + epsilon

            if decisionReached:
                break

            fixRDV.append(RDV)
            fixItem.append(currFixItem)
            fixTime.append(currFixTime - (currFixTime % timeStep))
            trialTime += currFixTime - (currFixTime % timeStep)

            # Sample and iterate over transition time.
            transitionTime = np.random.choice(fixationData.transitions)
            for t in xrange(int(transitionTime // timeStep)):
                # Sample the change in RDV from the distribution.
                RDV += np.random.normal(0, self.sigma)

                # If the RDV hit one of the barriers, the trial is over.
                if RDV >= self.barrier or RDV <= -self.barrier:
                    if RDV >= self.barrier:
                        choice = -1
                    elif RDV <= -self.barrier:
                        choice = 1
                    fixRDV.append(RDV)
                    fixItem.append(0)
                    fixTime.append(((t + 1) * timeStep) + motorDelay)
                    trialTime += (((t + 1) * timeStep) + motorDelay)
                    RT = trialTime
                    uninterruptedLastFixTime = currFixTime
                    decisionReached = True
                    break

            if decisionReached:
                break

            # Sample the next fixation for this trial.
            if currFixItem == 1:
                currFixItem = 2
            elif currFixItem == 2:
                currFixItem = 1
            valueDiff = fixUnfixValueDiffs[currFixItem]
            currFixTime = np.random.choice(
                fixationData.fixations[fixNumber][valueDiff])
            if fixNumber < numFixDists:
                fixNumber += 1

        return aDDMTrial(RT, choice, valueLeft, valueRight, fixItem, fixTime,
                         fixRDV)


    def get_model_likelihood(self, fixationData, trialConditions,
                             numSimulations, histBins, dataHistLeft,
                             dataHistRight):
        """
        Computes the likelihood of a data set given the parameters of the aDDM.
        Data set is provided in the form of reaction time histograms
        conditioned on choice.
        Args:
          fixationData: a FixationData object.
          trialConditions: list of pairs corresponding to the different trial
              conditions. Each pair contains the values of left and right
              items.
          numSimulations: integer, number of simulations per trial condition to
              be generated when creating reaction time histograms.
          histBins: list of numbers corresponding to the time bins used to
              create the reaction time histograms.
          dataHistLeft: dict indexed by trial condition (where each trial
              condition is a pair (valueLeft, valueRight)). Each entry is a
              numpy array corresponding to the reaction time histogram
              conditioned on left choice for the data. It is assumed that this
              histogram was created using the same time bins as argument
              histBins.
          dataHistRight: same as dataHistLeft, except that the reaction time
              histograms are conditioned on right choice.
          Returns:
              The likelihood for the given data and model.
        """
        likelihood = 0
        for trialCondition in trialConditions:
            RTsLeft = list()
            RTsRight = list()
            sim = 0
            while sim < numSimulations:
                try:
                    addmTrial = self.simulate_trial(
                        trialCondition[0], trialCondition[1], fixationData)
                except:
                    print("An exception occurred while generating " +
                          "artificial trial " + str(sim) + " for condition " +
                          str(trialCondition[0]) + ", " +
                          str(trialCondition[1]) + ", during the likelihood " +
                          "computation for model " + str(self.params) + ".")
                    raise
                if addmTrial.choice == -1:
                    RTsLeft.append(addmTrial.RT)
                elif addmTrial.choice == 1:
                    RTsRight.append(addmTrial.RT)
                sim += 1

            simulLeft = np.histogram(RTsLeft, bins=histBins)[0]
            if np.sum(simulLeft) != 0:
                simulLeft = simulLeft / float(np.sum(simulLeft))
            with np.errstate(divide='ignore'):
                logSimulLeft = np.where(simulLeft > 0, np.log(simulLeft), 0)
            dataLeft = np.array(dataHistLeft[trialCondition])
            likelihood += np.dot(logSimulLeft, dataLeft)

            simulRight = np.histogram(RTsRight, bins=histBins)[0]
            if np.sum(simulRight) != 0:
                simulRight = simulRight / float(np.sum(simulRight))
            with np.errstate(divide='ignore'):
                logSimulRight = np.where(simulRight > 0, np.log(simulRight), 0)
            dataRight = np.array(dataHistRight[trialCondition])
            likelihood += np.dot(logSimulRight, dataRight)

        return likelihood


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-threads", type=int, default=9,
                        help="Size of the thread pool.")
    parser.add_argument("--subject-ids", nargs="+", type=str, default=[],
                        help="List of subject ids. If not provided, all "
                        "existing subjects will be used.")
    parser.add_argument("--num-trials", type=int, default=10,
                        help="Number of artificial data trials to be "
                        "generated per trial condition.")
    parser.add_argument("--num-simulations", type=int, default=10,
                        help="Number of simulations to be generated per trial "
                        "condition, to be used in the RT histograms.")
    parser.add_argument("--bin-step", type=int, default=100,
                        help="Size of the bin step to be used in the RT "
                        "histograms.")
    parser.add_argument("--max-rt", type=int, default=8000,
                        help="Maximum RT to be used in the RT histograms.")
    parser.add_argument("--d", type=float, default=0.006,
                        help="aDDM parameter for generating artificial data.")
    parser.add_argument("--sigma", type=float, default=0.08,
                        help="aDDM parameter for generating artificial data.")
    parser.add_argument("--theta", type=float, default=0.5,
                        help="aDDM parameter for generating artificial data.")
    parser.add_argument("--range-d", nargs="+", type=float,
                        default=[0.005, 0.006, 0.007],
                        help="Search range for parameter d.")
    parser.add_argument("--range-sigma", nargs="+", type=float,
                        default=[0.065, 0.08, 0.095],
                        help="Search range for parameter sigma.")
    parser.add_argument("--range-theta", nargs="+", type=float,
                        default=[0.4, 0.5, 0.6],
                        help="Search range for parameter theta.")
    parser.add_argument("--expdata-file-name", type=str, default="expdata.csv",
                        help="Name of experimental data file.")
    parser.add_argument("--fixations-file-name", type=str,
                        default="fixations.csv",
                        help="Name of fixations file.")
    parser.add_argument("--verbose", default=False, action="store_true",
                        help="Increase output verbosity.")
    args = parser.parse_args()

    pool = Pool(args.num_threads)

    # Load experimental data from CSV file.
    if args.verbose:
        print("Loading experimental data...")
    data = load_data_from_csv(
        args.expdata_file_name, args.fixations_file_name, useAngularDists=True)

    # Get fixation distributions.
    if args.verbose:
        print("Getting fixation distributions...")
    subjectIds = args.subject_ids if args.subject_ids else None
    fixationData = get_empirical_distributions(data, subjectIds=subjectIds)

    histBins = range(0, args.max_rt + args.bin_step, args.bin_step)

    orientations = range(-15,20,5)
    trialConditions = list()
    for oLeft in orientations:
        for oRight in orientations:
            if oLeft != oRight:
                vLeft = np.absolute((np.absolute(oLeft) - 15) / 5)
                vRight = np.absolute((np.absolute(oRight) - 15) / 5)
                trialConditions.append((vLeft, vRight))

    # Generate histograms for artificial data.
    dataHistLeft = dict()
    dataHistRight = dict()
    model = aDDM(args.d, args.sigma, args.theta)
    for trialCondition in trialConditions:
        RTsLeft = list()
        RTsRight = list()
        trial = 0
        while trial < args.num_trials:
            try:
                aDDMTrial = model.simulate_trial(
                    trialCondition[0], trialCondition[1], fixationData)
            except:
                print("An exception occurred while generating artificial " +
                      "trial " + str(trial) + " for condition " +
                      str(trialCondition[0]) + ", " + str(trialCondition[1]) +
                      ".")
                raise
            if aDDMTrial.choice == -1:
                RTsLeft.append(aDDMTrial.RT)
            elif aDDMTrial.choice == 1:
                RTsRight.append(aDDMTrial.RT)
            trial += 1
        dataHistLeft[trialCondition] = np.histogram(RTsLeft, bins=histBins)[0]
        dataHistRight[trialCondition] = np.histogram(RTsRight,
                                                     bins=histBins)[0]

    if args.verbose:
        print("Done generating histograms of artificial data!")
    
    # Grid search on the parameters of the model.
    if args.verbose:
        print("Performing grid search over the model parameters...")
    listParams = list()
    models = list()
    for d in args.range_d:
        for sigma in args.range_sigma:
            for theta in args.range_theta:
                model = aDDM(d, sigma, theta)
                models.append(model)
                listParams.append((model, fixationData, trialConditions,
                                   args.num_simulations, histBins,
                                   dataHistLeft, dataHistRight))
    likelihoods = pool.map(wrap_addm_get_model_likelihood, listParams)
    pool.close()

    if args.verbose:
        for i, model in enumerate(models):
            print("L" + str(model.params) + " = " + str(likelihoods[i]))
        bestIndex = likelihoods.index(max(likelihoods))
        print("Best fit: " + str(models[bestIndex].params))


if __name__ == '__main__':
    main()
