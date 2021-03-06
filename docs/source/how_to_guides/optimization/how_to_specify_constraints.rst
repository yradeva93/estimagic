===========================
How to specify constraints
===========================

General structure of constraints
================================

The argument ``constraints`` of the estimagic functions `minimize` and `maximize`
can take a list with any number of constraints. Each constraint is specified with
a dictionary:

 .. code-block:: python

     constraints = [
         {"loc": "a", "type": "sdcorr"},  # first constraint
         {"loc": "b", "type": "fixed"},  # second constraint
     ]

     # pass the constraints to `minimize`
     results = minimize(
         criterion_function,
         params=params,
         constraints=constraints,
         algorithm="nlopt_bobyqa",
         algo_options={"maxeval": 200},
     )

The following keys are mandatory for all types of constraints:

- "loc" or "query", but not both:
    This will select the subset of parameters to which the constraint applies.
    If you use "loc", the corresponding value can be any expression that is
    valid for DataFrame.loc. If you are not familiar with these methods,
    check out our tutorial on selecting parameters.

- "type":
    The type of constraint to implement.

Depending on the type of constraints, some additional entries in the constraint
dictionary might be required. Below we show you how to specify constraints with
simplified examples.

Examples
========
In all the examples, we denote the parameters' DataFrame by ``"df"``.
Keep in mind the params DataFrame we used to explain how to select parameters,
where the first-level index denotes the parameter's category and the second-level
index further characterizes the parameter: For instance, specifying the parameter's
name if multiple parameters belong to the same category, or the time period if
the model is dynamic.

If you are unfamiliar with ``DataFrame.loc`` and ``DataFrame.query`` make sure
that your read that explanation first!

.. raw:: html

    <div class="container">
    <div id="accordion" class="shadow tutorial-accordion">

        <div class="card tutorial-card">
            <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseOne">
                <div class="d-flex flex-row tutorial-card-header-1">
                    <div class="d-flex flex-row tutorial-card-header-2">
                        <button class="btn btn-dark btn-sm"></button>
                        Fixed constraints
                    </div>
                    <span class="badge gs-badge-link">

.. raw:: html

                    </span>
                </div>
            </div>
            <div id="collapseOne" class="collapse" data-parent="#accordion">
                <div class="card-body">

To diagnose what goes wrong in difficult optimizations you often want to fix
some of the parameters. You could just remove them from your parameter
vector, but it's very handy if the parameter vector that arrives in your
objective function always looks exactly the same.
estimagic can fix the parameters for you.

A good example of a parameter that is fixed is a discount factor in a structural model.
Assume this parameter has ``"delta"`` in the first index level and we want to fix
it at 0.95. Then, the constraint is:

.. code-block:: python

    constraints = [{"loc": "delta", "type": "fixed", "value": 0.95}]

Note that ``"value"`` is optional. If it is not specified, the parameter is fixed
at the value specified in the DataFrame.


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseTwo">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                            Probability  constraints
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseTwo" class="collapse" data-parent="#accordion">
                    <div class="card-body">

Probability constraints are similar to sum constraints, but they always sum to 1
and are all bound between 0 and 1. Let's assume we have a params DataFrame with
``"shares"`` in the fist index level, and we want to make sure that all the
parameters grouped in that category will sum up to 1.

The constraint will look as follows:

.. code-block:: python

    constraints = [{"loc": "shares", "type": "probability"}]


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseThree">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                           Increasing and decreasing constraints
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseThree" class="collapse" data-parent="#accordion">
                    <div class="card-body">

As the name suggests, increasing constraints ensure that the selected parameters
are increasing. The prime example are cutoffs in ordered choice models as for
example the `ordered logit model`_.

.. _ordered logit model: ../../getting_started/ordered_logit_example.ipynb

If the parameters to be selected have, say, ``cutoffs`` in the first index level,
the constraint looks as follows:

 .. code-block:: python

     constraints = [{"loc": "cutoffs", "type": "increasing"}]

Decreasing constraints are defined analogously.


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseFour">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                           Equality constraints
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseFour" class="collapse" data-parent="#accordion">
                    <div class="card-body">

Equality constraints ensure that all selected parameters are equal. This may sound
useless, since one could simply leave all parameters except one out, but it often
makes the parsing of the parameter vector much easier.

For example, consider a dynamic model where you want to keep only certain parameters
time-invariant: The implementation can be much easier if you simply specify
a constraint with estimagic, rather than handling each case with an if-condition.

Consider a DataFrame where the first index level specify the parameter's
name, while the second index level enumerate periods in the model. Keeping the
parameter ``"a"`` time-invariant would be as simple as:

.. code-block:: python

    df.loc["a", "value"] = 2  # make sure "a" has the same value in each period
    constraints = [{"loc": "a", "type": "equality"}]

Under the hood this will optimize over just one parameter ``"a"`` and set the other
parameters ``"a"`` equal to it.


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseFive">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                           Pairwise equality constraints
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseFive" class="collapse" data-parent="#accordion">
                    <div class="card-body">

Pairwise equality constraints are different from all other constraints because
they correspond to several sets of parameters. Let's assume we want to keep the
parameters under group ``"a"`` and ``"b"`` pairwise equal. Then, the constraint
looks like this:

.. code-block:: python

    constraints = [{"locs": ["a", "b"], "type": "pairwise_equality"}]

Alternatively, you could have an entry ``"queries"`` where the corresponding value
is a list of query strings. Both ``"locs"`` and ``"queries"`` can have any number
of entries.


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseSix">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                           Covariance constraints
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseSix" class="collapse" data-parent="#accordion">
                    <div class="card-body">

In maximum likelihood estimation, you often have to estimate the covariance matrix
of a contribution. The covariance constraints makes sure that this covariance matrix
is valid, i.e. positive semi-definite.

Consider an example taken from the `respy <https://respy.readthedocs.io/en/latest/>`_
package, which provides a general framework to implement some discrete choice dynamic
programming (DCDP) models. A `toy model <https://tinyurl.com/y3e5hmo3>`_ implemented in
``respy`` represents a Robinson Crusoe economy, where in each period Robinson can choose
between fishing and relaxing in his hammock. The reward of each alternative is subject
to a shock, distributed according to a covariance matrix.

Let's say that the covariance matrix parameters are the ones where ``"category"``
equals "shocks_cov". The constraint could not be easier to express:

.. code-block:: python

    constraints = [{"loc": "shocks_cov", "type": "covariance"}]


estimagic will interpret the parameters selected by the constraint's ``"loc"`` or
``"query"`` field as the  **C-ordered lower triangle of a covariance matrix**,
starting with the first and only non-zero element of the first row, then the first
and second element of the second row and so on.

Note that the selected parameters will be interpreted this way regardless of the
parameters' names in the index.  Otherwise estimagic would have to make assumptions
on your index, and we don't want to do that.

To look at the resulting covariance matrix, we can use another estimagic function:

.. code-block:: python

    from estimagic.optimization.utilities import cov_params_to_matrix

    cov_params_to_matrix(df.loc["shocks_cov", "value"])

**Covariance constraints are not compatible with any other type of constraint,**
including box constraints. You don't have to add box constraints to keep the
variances positive because estimagic does this for you.

Some optimizers are more aggressive than others and test more extreme parameters,
which means that the variance-covariance matrix may not be positive semi-definite
for every proposed parameterization.

Internally, estimagic uses the Cholesky factor :math:`C`, a lower-triangular matrix,
of the variance-covariance matrix to do unconstrained optimization and rebuild
the variance-covariance with :math:`\Omega = CCT`. To ensure positive semi-definiteness,
you can add ``{"bounds_distance": 1e-6}`` to your constraint to bound the diagonal
elements of the Cholesky factor farther away from zero.

The complete constraint with distance to the bounds is:

.. code-block:: python

    constraints = [{"loc": "shocks_cov", "type": "covariance", "bounds_distance": 1e-6}]


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseSeven">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                           sdcorr constraints
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseSeven" class="collapse" data-parent="#accordion">
                    <div class="card-body">

Most of the time, it is more intuitive to look at standard deviations and correlations
than at covariance matrices. If this is the case, you want to use an "sdcorr"
constraint instead of the "covariance" constraint.

The sdcorr constraint assumes that that the first elements are standard deviations
and the rest is the lower triangle (excluding the diagonal) of a correlation matrix.
Again, the names in the index are ignored by estimagic.

The constraint is then just:

.. code-block:: python

    constraints = [{"loc": "shocks_sdcorr", "type": "sdcorr"}]

And, of course, there is another helper function in the utilities module:

.. code-block:: python

    from estimagic.optimization.utilities import sdcorr_params_to_sds_and_corr

    sds, corr = sdcorr_params_to_sds_and_corr(df.loc["shocks_sdcorr", "value"])

Note that the "bounds_distance" option is also available for "sdcorr" constraints.
See the previous section on covariance constraints for more information.


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseEight">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                           Linear constraints
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseEight" class="collapse" data-parent="#accordion">
                    <div class="card-body">

Linear constraints can be used to express constraints of the form
:code:`lower <=  weights.dot(x) <= upper` or :code:`weights.dot(x) = value`,
where x are the selected parameters. They have many of the above constraints as
special cases: You should only write a linear constraint if you can't express
it as one of the special cases.

Besides ``loc``, ``query`` and ``type``, linear constraints have the following
additional fields:

- weights:
    This will be used to construct the vector of weights. It can be a numpy array,
    pandas Series, list or a float. In the latter case, the weights for all selected
    parameters will be equal to that number.
- value:
    float
- lower:
    float
- upper:
    float

You can specify either value or lower and upper bounds. Suppose you have the
following params DataFrame:

.. table::
   :class: rows

   +-------------------+-------+
   |                   | value |
   +----------+--------+-------+
   | category | period |       |
   +==========+========+=======+
   |          |   0    |   2   |
   |    a     +--------+-------+
   |          |   1    |   1   |
   +----------+--------+-------+
   |          |   0    |   1   |
   |    b     +--------+-------+
   |          |   1    |   3   |
   +----------+--------+-------+
   |          |   0    |   1   |
   |    c     +--------+-------+
   |          |   1    |   1   |
   +----------+--------+-------+


Suppose you want to express the following constraints:

- The first parameter in the category ``"a"`` is two times the second parameter
  in that category.
- The mean of the ``"b"`` parameters is larger than 3
- The sum of the ``"c"`` parameters is between 0 and 5

Then the constraints would look as follows:

.. code-block:: python

    constraints = [
        {"loc": "a", "type": "linear", "weights": [1, -2], "value": 0},
        {"loc": "b", "type": "linear", "weights": 1 / 2, "lower": 3},
        {"loc": "c", "type": "linear", "weights": 1, "lower": 0, "upper": 5},
    ]


.. raw:: html

                        </span>
                    </div>
                </div>
            </div>

            <div class="card tutorial-card">
                <div class="card-header collapsed card-link" data-toggle="collapse" data-target="#collapseNine">
                    <div class="d-flex flex-row tutorial-card-header-1">
                        <div class="d-flex flex-row tutorial-card-header-2">
                            <button class="btn btn-dark btn-sm"></button>
                           Constraint killers
                        </div>
                        <span class="badge gs-badge-link">

.. raw:: html

                        </span>
                    </div>
                </div>
                <div id="collapseNine" class="collapse" data-parent="#accordion">
                    <div class="card-body">

All constraints can have an additional key called "id". An example could be:

.. code-block:: python

    constraints = [
        {"loc": "a", "type": "equality", "id": 0},
        {"loc": "b", "type": "increasing", "id": 1},
    ]

In structural economic models, the list of constraints can become quite large
and cumbersome to write. Therefore, packages that implement such models will
often write the constraints for you, and only allow you to complement them with
additional user constraints.

But what if you want to relax some of the constraints they implement automatically?
For this we have constraint killers. They take the following form:

.. code-block:: python

    killer = {"kill": 0}

For example, the following two lists of constraints will be equivalent:

.. code-block:: python

    constraints1 = [
        {"loc": "a", "type": "equality", "id": 0},
        {"loc": "b", "type": "increasing", "id": 1},
        {"kill": 0},
    ]
    constraints2 = [{"loc": "b", "type": "increasing", "id": 1}]

If you write a package that implements constraints for the user, the following are
best practices:

- Give the user the chance to add additional constraints.
- Add "id" entries to all constraints.
- Give the user the possibility to look at the constraints that were constructed
  automatically.
