# Simulations

The `run_simulations.py` script feeds a set of input conditions through the classifiers and outputs their results to file.

The intent is to gather outputs for comparing and tracking behavior of the classifiers.


## Inputs
The input file is expected to be a csv with two columns, representing the text to classify and (optional) the expected classification code.
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


## Getting sample contentions and classifications from Datadog

We can leverage application logging visible in Datadog Log Explorer to create sample inputs for simulations.

Among other data points, the logs show:
1) the text of the contention that the API was asked to classify
2) the name and code of the classification (or null values, if the csv lookup was unable to classify the contention)
3) the type of contention: whether it was submitted as a new condition, or as a claim for an increased disability rating ("claim for increase", CFI).


The Datadog Log Explorer allows for downloading results to a CSV file, which can then be further processed for compatibility with the simulator script.  Screenshot of the "Download as CSV" option:
<img src='https://github.com/user-attachments/assets/3b8f8ef9-1863-47ff-9adf-3544bba6096f' alt='screenshot of the "Download as CSV" option in Datadog' width=400/>


> For more about what data points are logged, see `def log_contention_stats()` and `def log_expanded_contention_text()` in [util/logging_utilities.py](https://github.com/department-of-veterans-affairs/contention-classification-api/blob/main/src/python_src/util/logging_utilities.py).


The search parameters for contention texts covered by the CSV lookup:

| tag | description |
| --- | --- |
| `index:main` | limit to the production environment  |
| `service:contention-classification-api` | limit to service `contention-classification-api`  |
| `-@contention_text:*unmapped*` |  exclude logs that have an attribute named `contention_text` that contains substring `unmapped` |
| `@classification_code:*` | limit to logs that have a value for attribute `classification_code`  |
| `@classification_name:*` |  limit to logs that have a value for attribute `classification_name`   |

[Link](https://vagov.ddog-gov.com/logs?query=service%3Acontention-classification-api%20%40classification_code%3A%2A%20%40classification_name%3A%2A&agg_m=count&agg_m_source=base&agg_t=count&clustering_pattern_field_path=%40contention_text&cols=%40contention_text%2C%40classification_code%2C%40classification_name&fromUser=true&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=stream&from_ts=1751728044281&to_ts=1751900844281&live=true) to this query in Datadog Log Explorer.

A sample of these results are in VA's Sharepoint (see https://github.com/department-of-veterans-affairs/vagov-claim-classification/issues/819).
