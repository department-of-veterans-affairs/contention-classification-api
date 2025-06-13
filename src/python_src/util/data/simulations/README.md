# Simulations

The `run_simulations.py` script feeds a set of input conditions through the classifiers and outputs their results to file.

The intent is to gather outputs for comparing and tracking behavior of the classifiers.


## Inputs 
The input file is expected to be a csv with these columns: text_to_classify, expected_classification
As an example of rows in an input file:

```
acne,9016
adjustment disorder,8989
agoraphobia,8989
alopecia,9016
```

## Outputs 

For each classifier being considered, two files are created:

1. a txt file that shows computed scores for the classifier (eg accuracy, precision, recall)
2. a csv file that shows the predictions made by the classifier for the inputs.
As an example of rows in this output file:

```
text_to_classify,expected_classification,prediction,is_accurate
acne,9016,9016,True
adjustment disorder,8989,,False
agoraphobia,8989,8989,True
alopecia,9016,1234,False
```

Additionally,if more than one classifier is being considered, then an output file of the predictions across all of the classifiers is created.
As an example of rows in this output file:
```
text_to_classify,expected_classification,prediction_by_model_a,is_model_a_accurate,prediction_by_model_b,is_model_b_accurate
acne,9016,9016,True,9012,False
adjustment disorder,8989,9012,False,8989,True
agoraphobia,8989,8989,True,8989,True
alopecia,9016,1234,False,9012,False
```

## Usage

Usage: (from the codebase root directory)
```
poetry run python src/python_src/util/data/simulations/run_simulations.py
```
