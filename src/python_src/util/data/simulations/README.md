# Simulations

The `run_simulations.py` script feeds a set of input conditions through the classifiers and outputs their results to file.

The intent is to gather outputs for comparing and tracking behavior of the classifiers.


## Inputs
The input file is expected to be a csv with these columns: text_to_classify, expected_classification.   
As an example of rows in an input file:

```
acne,9016
adjustment disorder,8989
agoraphobia,8989
alopecia,9016
```

## Outputs

For each classifier being considered, two files are created:

1. a txt file that shows computed metrics for the classifier (eg accuracy, precision, recall)  
As an example of this file:
```
              precision    recall  f1-score   support

        8968       1.00      0.00      0.00         1
        9012       1.00      0.00      0.00         3
        9016       0.60      1.00      0.75         6

    accuracy                           0.60        10
   macro avg       0.87      0.33      0.25        10
weighted avg       0.76      0.60      0.45        10

``` 
(where `8968`, `9012`, and `9016` are the possible classifications)


2. a csv file that shows the predictions made by the classifier for the inputs.  
As an example of rows in this output file:

```
text_to_classify,expected_classification,prediction,is_accurate
acne,9016,9016,True
adjustment disorder,8989,,False
agoraphobia,8989,8989,True
alopecia,9016,1234,False
```

Additionally, if more than one classifier is being considered, then an output file of the predictions across all of the classifiers is created.  
As an example of rows in this output file:
```
text_to_classify,expected_classification,model_a_prediction,model_a_is_accurate,model_b_prediction,is_model_b_accurate
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
