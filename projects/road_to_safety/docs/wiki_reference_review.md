# AI wiki reference review for Road to Safety

Reviewed October 18, 2026. This is a methodological review and proposed integration plan, not a new fitted experiment. The frozen severity protocol, fitted coefficients, predictions and evaluation receipts remain unchanged. The reference wiki was read without modification.

## Scope and evidence

I inspected the wiki index, searched the wiki for calibration, temporal validation, imbalance, drift, uncertainty and related concepts, and read the relevant method/concept/source summaries. I also checked selected passages in the local Géron and Peixeiro books. This was a targeted project review, not a cover-to-cover review of the raw library.

The wiki is useful as a conceptual and bibliographic index. Some pages are brief syntheses or broad recommendations rather than validated implementation recipes. Calibration details were supplemented with the official scikit-learn 1.7 documentation, matching the project's installed major/minor version. Recommendations below are adaptations to this collision dataset, not instructions copied indiscriminately from the wiki.

## What is already integrated

The project already implements several central wiki principles: interpretable regularized modeling, explicit train/validation/test separation, chronological evaluation, precision–recall reporting for an imbalanced outcome, reproducible pipelines, unknown/other preservation, model cards, conditional-association language and visually inspected diagnostic charts. These do not need to be rebuilt merely because the wiki recommends them.

The current model's limitations identify where additional methods can help: test mean prediction is 1.6036% versus observed fatal proportion 1.9746%; the illustrative threshold yields 82.11% recall but 2.92% precision while flagging 55.59% of test collisions. There is one retrospective temporal test period and no predeclared uncertainty intervals. These are the priorities before a more complex model.

## Integration priorities

| Priority | Wiki reference | Proposed project integration | Evidence/output needed |
|---|---|---|---|
| Immediate | [Cross-validation](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/methods/cross-validation.md), Peixeiro's time-series validation discussion | Several expanding-window development evaluations using explicit whole-year boundaries; separate model-fit, calibration-fit and subsequent evaluation periods | Frozen fold manifest and per-year scores, with all transforms/calibrators trained before the evaluated year |
| Immediate | [Concept drift](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/concept-drift.md), [model monitoring](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/model-monitoring.md) | Retrospective drift diagnostics: feature shares, unknown/other shares, outcome prevalence and probability calibration across folds | Distinguish input-distribution changes, outcome-prevalence changes and evidence concerning conditional performance; no claim that the cause has been identified |
| Immediate | [Uncertainty quantification](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/uncertainty-quantification.md), with official calibration guidance | Compare unchanged probabilities with simple, separately fitted calibration candidates; examine the low-probability range in greater detail | Proper scores plus calibration intercept/slope, observed/expected outcomes, bins with event counts and plots; no promise that older calibration transfers through a later shift |
| Next | [Evaluation metrics](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/methods/evaluation-metrics.md), Géron's precision–recall discussion | Threshold tradeoff tables showing precision, recall, false positives and fraction flagged at predeclared illustrative capacities | All cutoffs chosen using development data only; operational costs/capacity require a defined use case rather than an assumed universal optimum |
| Next | [Bootstrap](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/bootstrap.md), ISLR resampling reference | Paired uncertainty assessment of score differences on the same evaluated collisions, alongside variation across temporal folds | State resampling unit and assumptions; distinguish fixed-model conditional uncertainty from training uncertainty and future-year variation |
| Later | [Feature engineering](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/feature-engineering.md), [ensemble methods](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/ensemble-methods.md) | A small, predeclared interaction model, such as hour×weekday or weather×surface, before considering one tree-based challenger | Select within pre-2020 development folds, preserve the allowlist and category rules, compare proper scores and calibration as well as ranking; gains are hypotheses, not guaranteed |
| Before policy claims | [Causal inference](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/causal-inference.md), [confounding](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/confounding.md), [structural causal models](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/structural-causal-models.md) | A causal-assumption diagram and an evidence ledger separating observed associations from intervention claims | Record absent speed, geographic, exposure and road-user context; discuss selection into the fatal/injury cohort. A diagram does not identify an intervention effect from missing information |
| After new data | [Geographic data science](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/geographic-data-science.md), [spatial autocorrelation](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/spatial-autocorrelation.md) | Spatially appropriate mapping, joins and validation | Verified jurisdiction/location fields, compatible boundaries and denominators. The current collision table cannot support local hotspots, spatially blocked collision validation or inferred coordinates |

## Important adaptations and limits

### Temporal validation must match the available clock

The wiki lists ordinary and stratified K-fold validation alongside a temporal variant. For this project, use chronological year groups. Random or class-stratified splitting would mix source periods and would not answer future-year generalization.

The collision records are event observations, not equally spaced time samples, and lack full calendar dates. Therefore use explicit year cutoffs instead of applying a row-count splitter blindly. The official [TimeSeriesSplit documentation](https://scikit-learn.org/1.7/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) explains its equal-spacing assumption for comparable fold durations. The reusable idea is expanding temporal evaluation, not a requirement to use that class directly.

Peixeiro's local book describes preserving time order, fitting an initial historical subset and evaluating successive later horizons (section 19.4.2). We can adapt that validation principle to collision severity without changing the task into time-series forecasting or fitting Prophet/ARIMA.

### Calibration is a separate experiment

The wiki's uncertainty page emphasizes probabilistic reliability, but is mainly about neural-network uncertainty and does not supply a complete rare-event temporal-calibration protocol. Bayesian/deep models do not automatically solve this project's calibration gap, and uncertainty quantification is not interchangeable with calibration.

A small candidate set is sufficient initially: unmodified probabilities, intercept-only logistic recalibration, and sigmoid recalibration. Define the exact input scale and fitting rules in a new protocol. Keep all calibration labels later than the estimator's training years and earlier than the evaluation year. The official [calibration guide](https://scikit-learn.org/1.7/modules/calibration.html) supports disjoint classifier/calibrator data and describes sigmoid/isotonic methods. This review proposes the intercept-only comparison as a project-specific simple alternative, not as a method already documented in the wiki.

Lower Brier/log loss is useful but does not by itself prove better calibration: these scores also reflect discrimination. Use direct calibration diagnostics as well. That distinction is explicit in the same [official guide](https://scikit-learn.org/1.7/modules/calibration.html). Retain the original ten-bin results as the frozen baseline; add separately labeled, prespecified finer/equal-frequency diagnostics within the new experiment. Most current scores are below 0.1, so the old first bin conceals much of that range.

The 2020–2021 underprediction is observed evidence of a calibration change. Input-share changes and higher outcome prevalence do not, on their own, establish the mechanism or prove a specific form of conditional concept drift. A correction fitted before that change may still fail to transfer. Do not calibrate on 2020–2021 labels and then call performance on those same years independent validation.

### Uncertainty needs a defined target

For a fixed saved model, a paired collision bootstrap can estimate sampling variability of differences such as model-minus-baseline log loss under the stated within-year independence assumptions. Resample the same collision indices for both models; otherwise the comparison discards pairing. Stratify by evaluated year if preserving year composition is the target.

Such intervals do not cover all training uncertainty, hidden geographic dependence, source bias or future distribution changes. A two-year test set supplies only two temporal clusters; do not present a year-cluster bootstrap as robust evidence about future Canadian years. Report annual/fold differences directly. A separate design would be needed to quantify variability from refitting models.

Similarly, standard deviation across temporal folds is useful descriptive variation, not automatically a confidence interval: expanding training sets overlap and folds are not independent replicates.

### Predictive associations do not establish policy effects

The causal pages help articulate the research question and missing assumptions. Our model conditions on a recorded injury/fatal collision; this selected population can differ from all traffic exposure or all crashes. Conditioning on selection can also distort associations. More elaborate adjustment, matching or causal discovery cannot manufacture the absent population, covariates or intervention information.

Keep recommendations linked to external intervention evidence and compatible local data. Do not treat a regularized odds ratio, feature importance or a spatial cluster as a proven preventable effect.

### Model complexity is not the immediate bottleneck

The ensemble page's broad claims about tabular performance are reasons to consider a later comparator, not evidence that a tree ensemble will outperform this logistic model. Any such comparator needs the same temporal and calibration checks. Deep learning, Bayesian neural networks, graph models and reinforcement learning are not justified next additions for eight categorical predictors and the present task. LLMs can help organize narrative references; they do not provide verified missing collision labels, exposure or geographic data.

## Recommended next step: a new temporal robustness and calibration protocol

Preserve the completed baseline protocol and all artifacts. Create a separately versioned development protocol before any additional fitting. The baseline's 2020–2021 test outcomes have now been evaluated; stronger prospective evidence needs a newer audited record-level period or future observations.

A concrete proposed development design is:

1. Use evaluation years **2014–2019**. For evaluation year `t`, fit the fixed logistic estimator on **1999 through t−3**, fit any calibration adjustment on **t−2 through t−1**, and evaluate only on **t**. These are proposed boundaries, not frozen or executed in this review.
2. Compare unchanged scores, intercept-only recalibration and sigmoid recalibration. Keep the eight features, unknown/other categories and the existing target definition. Do not add interaction or tree searches to this first calibration experiment.
3. Predeclare exact formulas, model/calibrator fitting settings, probability clipping, sparse/bin rules, any selection rule and the uncertainty assumptions. Retain a training-prevalence comparator and the original frozen run for context. A calibration-period prevalence comparator can be labeled separately if prespecified; do not silently redefine the baseline.
4. Report log loss, Brier, average precision, ROC-AUC, direct calibration diagnostics, count support and performance by year and feature-availability status. Compare methods on the same observations. Assess whether gains persist across several years rather than only in a pooled average.
5. Keep 2020–2021 out of method selection. If the final fixed procedure is subsequently reapplied there, label it a **reused retrospective stress test**, not a newly untouched holdout. Pre-2020 folds themselves are development evidence because prior EDA and baseline reporting have already used these years.
6. Document failure as well as improvement. If calibration does not transfer, do not overwrite the original model or repeatedly tune on the stress years. The deliverable is an auditable robustness/calibration comparison and updated interpretation, even if no candidate is reliably better.

No fit, parameter change, calibration correction, new split artifact or wiki write was performed as part of this review.

## References inspected

The integration table links the principal wiki pages. Additional local references inspected include [ISLR source summary](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/sources/james-islr-2013.md), [ML systems source summary](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/sources/huyen-designing-ml-systems-2022.md), and [visualization in predictive modeling](/Users/micra/Dataland/Wiki_Inteligencia_Artificial/knowledge_AI/wiki/concepts/visualization-in-predictive-modeling.md). Selected raw-book passages were checked in Géron's chapter 3 precision–recall discussion and Peixeiro's section 19.4.2 temporal cross-validation discussion. Original source pages should be consulted again for implementation-specific claims rather than treating the wiki summary as a full specification.
