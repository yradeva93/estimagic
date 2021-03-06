"""This module implements the POUNDERs algorithm."""
import functools

import numpy as np

from estimagic.config import IS_PETSC4PY_INSTALLED
from estimagic.optimization.algo_options import CONVERGENCE_ABSOLUTE_GRADIENT_TOLERANCE
from estimagic.optimization.algo_options import CONVERGENCE_RELATIVE_GRADIENT_TOLERANCE
from estimagic.optimization.algo_options import CONVERGENCE_SCALED_GRADIENT_TOLERANCE
from estimagic.optimization.algo_options import STOPPING_MAX_ITERATIONS
from estimagic.optimization.utilities import calculate_trustregion_initial_radius

try:
    from petsc4py import PETSc
except ImportError:
    pass

POUNDERS_ALGO_INFO = {
    "primary_criterion_entry": "root_contributions",
    "parallelizes": False,
    "needs_scaling": True,
    "name": "tao_pounders",
}


def tao_pounders(
    criterion_and_derivative,
    x,
    lower_bounds,
    upper_bounds,
    *,
    convergence_absolute_gradient_tolerance=CONVERGENCE_ABSOLUTE_GRADIENT_TOLERANCE,
    convergence_relative_gradient_tolerance=CONVERGENCE_RELATIVE_GRADIENT_TOLERANCE,
    convergence_scaled_gradient_tolerance=CONVERGENCE_SCALED_GRADIENT_TOLERANCE,
    trustregion_initial_radius=None,
    stopping_max_iterations=STOPPING_MAX_ITERATIONS,
):
    r"""Minimize a function using the POUNDERs algorithm.

    Do not call this function directly but pass its name "tao_pounders" to estimagic's
    maximize or minimize function as `algorithm` argument. Specify your desired
    arguments as a dictionary and pass them as `algo_options` to minimize or
    maximize.

    POUNDERs (:cite:`Benson2017`, :cite:`Wild2015`, `GitLab repository
    <https://gitlab.com/petsc/petsc4py/-/tree/master>`_)
    can be a useful tool for economists who estimate structural models using
    indirect inference, because unlike commonly used algorithms such as Nelder-Mead,
    POUNDERs is tailored for minimizing a non-linear sum of squares objective function,
    and therefore may require fewer iterations to arrive at a local optimum than
    Nelder-Mead.

    The criterion function :func:`func` should return a dictionary with the following
    fields:

    1. ``"value"``: The sum of squared (potentially weighted) errors.
    2. ``"root_contributions"``: An array containing the root (weighted) contributions.

    Scaling the problem is necessary such that bounds correspond to the unit hypercube
    :math:`[0, 1]^n`. For unconstrained problems, scale each parameter such that unit
    changes in parameters result in similar order-of-magnitude changes in the criterion
    value(s).

    POUNDERs has several convergence criteria. Let :math:`X` be the current parameter
    vector, :math:`X_0` the initial parameter vector, :math:`g` the gradient, and
    :math:`f` the criterion function.

    ``absolute_gradient_tolerance`` stops the optimization if the norm of the gradient
    falls below :math:`\epsilon`.

    .. math::

        ||g(X)|| < \epsilon

    ``relative_gradient_tolerance`` stops the optimization if the norm of the gradient
    relative to the criterion value falls below :math:`epsilon`.

    .. math::

        ||g(X)|| / |f(X)| < \epsilon

    ``scaled_gradient_tolerance`` stops the optimization if the norm of the gradient is
    lower than some fraction :math:`epsilon` of the norm of the gradient at the initial
    parameters.

    .. math::

        ||g(X)|| / ||g(X0)|| < \epsilon

    Args:
        absolute_gradient_tolerance (float): Stop if relative norm of gradient is less
            than this. If set to False the algorithm will not consider
            absolute_gradient_tolerance.
        relative_gradient_tolerance (float): Stop if norm of gradient is less than this.
            If set to False the algorithm will not consider relative_gradient_tolerance.
        scaled_gradient_tolerance (float): Stop if norm of gradient is reduced by this
            factor. If set to False the algorithm will not consider
            relative_gradient_tolerance.
        trustregion_initial_radius (float): Initial value of the trust region radius.
            It must be :math:`> 0`.
        stopping_max_iterations (int): Alternative Stopping criterion.
            If set the routine will stop after the number of specified iterations or
            after the step size is sufficiently small. If the variable is set the
            default criteria will all be ignored.

    Returns:
        results (dict): Dictionary with processed optimization results.

    """
    if not IS_PETSC4PY_INSTALLED:
        raise NotImplementedError(
            "The petsc4py package is not installed and required for 'tao_pounders'. If "
            "you are using Linux or MacOS, install the package with 'conda install -c "
            "conda-forge petsc4py. The package is not available on Windows."
        )

    func = functools.partial(
        criterion_and_derivative,
        task="criterion",
        algorithm_info=POUNDERS_ALGO_INFO,
    )

    x = _initialise_petsc_array(x)
    # We need to know the number of contributions of the criterion value to allocate the
    # array.
    n_errors = len(
        criterion_and_derivative.keywords["first_criterion_evaluation"]["output"][
            "root_contributions"
        ]
    )
    residuals_out = _initialise_petsc_array(n_errors)

    # Create the solver object.
    tao = PETSc.TAO().create(PETSc.COMM_WORLD)

    # Set the solver type.
    tao.setType("pounders")

    tao.setFromOptions()

    def func_tao(tao, x, resid_out):
        """Evaluate objective and attach result to an petsc object f.

        This is required to use the pounders solver from tao.

        Args:
             tao: The tao object we created for the optimization task.
             x (PETSc.array): Current parameter values.
             f: Petsc object in which we save the current function value.

        """
        resid_out.array = func(x.array)

    # Set the procedure for calculating the objective. This part has to be changed if we
    # want more than pounders.
    tao.setResidual(func_tao, residuals_out)

    if trustregion_initial_radius is None:
        trustregion_initial_radius = calculate_trustregion_initial_radius(x)
    elif trustregion_initial_radius <= 0:
        raise ValueError("The initial trust region radius must be > 0.")
    tao.setInitialTrustRegionRadius(trustregion_initial_radius)

    # Add bounds.
    lower_bounds = _initialise_petsc_array(lower_bounds)
    upper_bounds = _initialise_petsc_array(upper_bounds)
    tao.setVariableBounds(lower_bounds, upper_bounds)

    # Put the starting values into the container and pass them to the optimizer.
    tao.setInitial(x)

    # Obtain tolerances for the convergence criteria. Since we can not create
    # scaled_gradient_tolerance manually we manually set absolute_gradient_tolerance and
    # or relative_gradient_tolerance to zero once a subset of these two is turned off
    # and scaled_gradient_tolerance is still turned on.
    default_gatol = (
        convergence_absolute_gradient_tolerance
        if convergence_absolute_gradient_tolerance
        else -1
    )
    default_gttol = (
        convergence_scaled_gradient_tolerance
        if convergence_scaled_gradient_tolerance
        else -1
    )
    default_grtol = (
        convergence_relative_gradient_tolerance
        if convergence_relative_gradient_tolerance
        else -1
    )
    # Set tolerances for default convergence tests.
    tao.setTolerances(
        gatol=default_gatol,
        grtol=default_grtol,
        gttol=default_gttol,
    )

    # Set user defined convergence tests. Beware that specifying multiple tests could
    # overwrite others or lead to unclear behavior.
    if stopping_max_iterations is not None:
        tao.setConvergenceTest(functools.partial(_max_iters, stopping_max_iterations))
    elif (
        convergence_scaled_gradient_tolerance is False
        and convergence_absolute_gradient_tolerance is False
    ):
        tao.setConvergenceTest(
            functools.partial(_grtol_conv, convergence_relative_gradient_tolerance)
        )
    elif (
        convergence_relative_gradient_tolerance is False
        and convergence_scaled_gradient_tolerance is False
    ):
        tao.setConvergenceTest(
            functools.partial(_gatol_conv, convergence_absolute_gradient_tolerance)
        )
    elif convergence_scaled_gradient_tolerance is False:
        tao.setConvergenceTest(
            functools.partial(
                _grtol_gatol_conv,
                convergence_relative_gradient_tolerance,
                convergence_absolute_gradient_tolerance,
            )
        )

    # Run the problem.
    tao.solve()

    results = _process_pounders_results(residuals_out, tao)

    # Destroy petsc objects for memory reasons.
    for obj in [tao, x, residuals_out, lower_bounds, upper_bounds]:
        obj.destroy()

    return results


def _initialise_petsc_array(len_or_array):
    """Initialize an empty array or fill in provided values.

    Args:
        len_or_array (int or numpy.ndarray): If the value is an integer, allocate an
            empty array with the given length. If the value is an array, allocate an
            array of equal length and fill in the values.

    """
    length = len_or_array if isinstance(len_or_array, int) else len(len_or_array)

    array = PETSc.Vec().create(PETSc.COMM_WORLD)
    array.setSizes(length)
    array.setFromOptions()

    if isinstance(len_or_array, np.ndarray):
        array.array = len_or_array

    return array


def _max_iters(max_iterations, tao):
    if tao.getSolutionStatus()[0] < max_iterations:
        return 0
    elif tao.getSolutionStatus()[0] >= max_iterations:
        tao.setConvergedReason(8)


def _gatol_conv(absolute_gradient_tolerance, tao):
    if tao.getSolutionStatus()[2] >= absolute_gradient_tolerance:
        return 0
    elif tao.getSolutionStatus()[2] < absolute_gradient_tolerance:
        tao.setConvergedReason(3)


def _grtol_conv(relative_gradient_tolerance, tao):
    if (
        tao.getSolutionStatus()[2] / tao.getSolutionStatus()[1]
        >= relative_gradient_tolerance
    ):
        return 0
    elif (
        tao.getSolutionStatus()[2] / tao.getSolutionStatus()[1]
        < relative_gradient_tolerance
    ):
        tao.setConvergedReason(4)


def _grtol_gatol_conv(relative_gradient_tolerance, absolute_gradient_tolerance, tao):
    if (
        tao.getSolutionStatus()[2] / tao.getSolutionStatus()[1]
        >= relative_gradient_tolerance
    ):
        return 0
    elif (
        tao.getSolutionStatus()[2] / tao.getSolutionStatus()[1]
        < relative_gradient_tolerance
    ):
        tao.setConvergedReason(4)

    elif tao.getSolutionStatus()[2] < absolute_gradient_tolerance:
        tao.setConvergedReason(3)


def _translate_tao_convergence_reason(tao_resaon):
    mapping = {
        3: "absolute_gradient_tolerance below critical value",
        4: "relative_gradient_tolerance below critical value",
        5: "scaled_gradient_tolerance below critical value",
        6: "step size small",
        7: "objective below min value",
        8: "user defined",
        -2: "maxits reached",
        -4: "numerical problems",
        -5: "max funcevals reached",
        -6: "line search failure",
        -7: "trust region failure",
        -8: "user defined",
    }
    return mapping[tao_resaon]


def _process_pounders_results(residuals_out, tao):
    convergence_code = tao.getConvergedReason()
    convergence_reason = _translate_tao_convergence_reason(convergence_code)

    results = {
        "solution_x": tao.solution.array,
        "solution_criterion": tao.function,
        "solution_derivative": None,
        "solution_hessian": None,
        "n_criterion_evaluations": tao.getIterationNumber(),
        "n_derivative_evaluations": None,
        "n_iterations": None,
        "success": True if convergence_code >= 0 else False,
        "reached_convergence_criterion": convergence_reason
        if convergence_code >= 0
        else None,
        "message": convergence_reason,
        # Further results.
        "solution_criterion_values": residuals_out.array,
        "gradient_norm": tao.gnorm,
        "criterion_norm": tao.cnorm,
        "convergence_code": convergence_code,
    }

    return results
