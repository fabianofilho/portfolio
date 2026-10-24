---
title: The feature ceiling
summary: Seven diabetes models, from a logistic regression to a tuned ensemble, all landed on the same AUC. What that tie says about the data, and why the next month of work belongs to the variables.
date: 2026-10-24
draft: false
---
We built a model to predict type 2 diabetes in a large health plan that owns its
hospitals, emergency rooms and labs, with one patient identifier linking primary care,
emergency, hospital and lab records. Each patient window carried twelve months of history
before the index date, and 38 features: thirteen lab tests, six comorbidity flags, how often the person
used the network, and the vital signs. Blood pressure, heart rate, weight and height came
from the free text of the doctors' notes, which we parsed with regular expressions.

Then we trained everything. A logistic regression, a random forest, histogram gradient
boosting, XGBoost and LightGBM each tuned with fifty rounds of Bayesian search, a voting
ensemble, and an isotonic-calibrated version of the best one. On the held-out test set,
all seven reached an area under the curve of 0.760, with the same 95% interval, 0.757 to
0.763. The logistic regression was as good as the ensemble. Fasting glucose, a history of
hypertension and urea carried most of the signal, which is what any endocrinologist
would have guessed.

That tie made me write a short viewpoint to give the pattern a name: the feature ceiling.
It is the point at which the information carried by the available variables sets the
limit on performance, whatever the algorithm. The viewpoint was accepted by JMIR AI in
September. The idea is simple, and in my experience teams almost never act on it. When
the models converge, the usual reaction is to book another round of hyperparameter
search.

Most of us learned to build prediction models as an engineering problem. Pick the
algorithm, tune it, make the pipeline robust, report the best number. All of that is
worth doing, and all of it assumes something nobody checks: that the features hold enough
information about the outcome. In our case they held enough for 0.76. Fifty more Optuna
trials could not change that, and the seven-way tie was the clearest evidence we were
ever going to get.

The useful questions come before the first model is trained. Which clinically relevant
variables are in the dataset, and which are missing because the system never captured
them? Is there missingness that follows the flow of care? Most members never made it into
our cohort, and the main reason was the lack of a single lab test in the previous year.
The people who do get tested are not a random sample. Do the features describe the patient over a window that
matches the outcome? Twelve months of history is a short look at a disease that takes
years to develop. These questions take an afternoon. Asked at the end, they explain the
disappointing result; asked at the start, they change the design.

They also show where the next gain is. The way up from 0.76 was never going to be a
bigger model. It was going to be something the model could not see: the glucose
trajectory over several years, prescriptions, diet and physical activity, family history,
where the person lives and what they earn. Some of that is probably in the same free-text notes
we mined for blood pressure. Some of it was never recorded anywhere. That work is slower
and less glamorous than tuning, and it is the work that moves the curve.

The ceiling is set long before anyone opens a notebook. The variables a model can use
were decided years earlier by whoever designed the intake form, chose which measurements
get their own field and decided which systems would talk to each other. That plan had an
advantage many health systems lack: one identifier across primary care, emergency,
hospital and lab. Where mortality, hospital and notification records were built as
separate systems, joining them still takes probabilistic linkage. A model trained on either
inherits those decisions.

I saw the same thing again in August, in a different kind of problem. Three forecasting
models of monthly cardiovascular deaths from a public mortality registry finished within 0.13 percentage
points of each other, and nine more years of history cut the error by 1.2 to 1.7 points.
More data beat every choice of model.

This matters more now that agents do most of the modelling. An agent can try forty model
families overnight and report the winner in a clean table. It will hit the ceiling faster
than we did, and it cannot raise it. It cannot add a field the system never recorded, or
ask the doctor why the weight goes into the note and not into a form field. The tie
between models used to take a team months to discover. Now it takes a night, and what the
team does the next morning is still ours to decide.

So I treat the feature ceiling as a diagnosis, made on purpose, with a short list of
checks at the design stage and a plan for what to do when the models converge. The
convergence is information about the data. Read it early, and spend the next month on
the variables.

*The viewpoint: [The Feature Ceiling: Recognizing Data-Driven Performance Limits as a Diagnostic Category in Clinical Machine Learning](https://doi.org/10.2196/preprints.96900), JMIR AI, 2026 (in press).*
