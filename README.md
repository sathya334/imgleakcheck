# leakcheck

A small tool that checks whether any of your test images secretly also exist in your training set.

I started thinking about this while working on a brain tumor MRI classifier. If the same scan ends up in both train and test (even resized, renamed, or saved as a different format), the model gets tested on something it has already seen, and the accuracy number stops meaning much. Checking this by hand is impossible once you have thousands of images, so I wrote this.



![A test image next to its copy in the train set](leak_0_leaked_0.png)



## Install

```bash
pip install leakcheck
```

## How to use it

Point it at your train and test folders:

```bash
leakcheck train/ test/
```

You'll get something like this:

```
LEAK  leaked_0.jpg  ~  train_0.png  (distance 0)
LEAK  leaked_1.jpg  ~  train_1.png  (distance 0)
...
5 of 25 test images (20.0%) also appear in train.
```

A few extra options:

```bash
leakcheck train/ test/ --csv leaks.csv       # save the results to a CSV file
leakcheck train/ test/ --show leak_pairs     # save side-by-side images so you can check them yourself
leakcheck train/ test/ --threshold 0         # only flag exact matches
```

The default threshold is 5. Raise it to catch more loosely similar images, or lower it if you're getting false alarms.

## How it works

Every image gets turned into a 64-bit "fingerprint" using perceptual hashing. Unlike a normal file hash, this fingerprint depends on what the image looks like, not on the exact bytes, so a resized or recompressed copy ends up with the same (or almost the same) fingerprint.

To compare two images, I count how many bits differ between their fingerprints. Zero means they're basically identical.

Comparing every test image with every train image gets slow fast, so the train fingerprints go into a BK-tree. It's a data structure built for "find anything within distance X" searches, and it uses the triangle inequality to skip big parts of the tree that can't contain a match.

## Tests

```bash
pip install pytest
pytest -v
```

One of the tests compares the BK-tree against a plain brute-force search on random data, to make sure the faster method never misses anything.

## License

MIT
