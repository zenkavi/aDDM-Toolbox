
**Q: In simulate trial is currFixLocation 0 only once in the beginning?**

Read in data

```
data = util.load_data_from_csv('/home/aDDM-Toolbox/addm_toolbox/data/single_sub_expdata.csv', '/home/aDDM-Toolbox/addm_toolbox/data/single_sub_fixations.csv')
```

Extract fixation data in the format defined in `addm.py`

```
fixationData = util.get_empirical_distributions(data)
```

Define model and simulate trial

```
m = addm.aDDM(d = 0.02, sigma = .02, theta = .1)
m.simulate_trial(valueLeft = data['0'][0].valueLeft, valueRight = data['0'][0].valueLeft, fixationData = fixationData)
```

**A: No! It always transition look one way, transition, look the other way.**

```
test_trial = m.simulate_trial(valueLeft = data['0'][0].valueLeft, valueRight = data['0'][0].valueLeft, fixationData = fixationData)
test_trial.fixItem
[0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2]
```

**Q: How does `get_empirical_distributions` organize its output in the `FixationData` object?**

What are the keys of `FixationData.fixations`?

 **A: Fixation numbers (i.e.first fixation, second fixation etc.). Defaults to binning fixations into 3 bins. If a trial has more than 3 fixations, the data on all the later fixations are stored in FixationData.fixations[3][valueDiff]**