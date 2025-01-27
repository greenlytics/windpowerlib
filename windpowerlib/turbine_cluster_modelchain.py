"""
The ``turbine_cluster_modelchain`` module contains functions and classes of the
windpowerlib. This module makes it easy to get started with the windpowerlib
and shows use cases for the power output calculation of wind farms and wind
turbine clusters.

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import logging
from windpowerlib import wake_losses
from windpowerlib.modelchain import ModelChain


class TurbineClusterModelChain(ModelChain):
    r"""
    Model to determine the output of a wind farm or wind turbine cluster.

    Parameters
    ----------
    power_plant : :class:`~.wind_farm.WindFarm` or :class:`~.wind_turbine_cluster.WindTurbineCluster`
        A :class:`~.wind_farm.WindFarm` object representing the wind farm or
        a :class:`~.wind_turbine_cluster.WindTurbineCluster` object
        representing the wind turbine cluster.
    wake_losses_model : str or None
        Defines the method for taking wake losses within the farm into
        consideration. Options: None, 'power_efficiency_curve' or
        'constant_efficiency' or the name of a wind efficiency curve like
        'dena_mean'. Default: 'dena_mean'.
        Use :py:func:`~.wake_losses.get_wind_efficiency_curve` for all provided
        wind efficiency curves.
    smoothing : bool
        If True the power curves will be smoothed before or after the
        aggregation of power curves depending on `smoothing_order`.
        Default: False.
    block_width : float
        Width between the wind speeds in the sum of the equation in
        :py:func:`~.power_curves.smooth_power_curve`. Default: 0.5.
    standard_deviation_method : str
        Method for calculating the standard deviation for the Gauss
        distribution. Options: 'turbulence_intensity', 'Staffell_Pfenninger'.
        Default: 'turbulence_intensity'.
    smoothing_order : str
        Defines when the smoothing takes place if `smoothing` is True. Options:
        'turbine_power_curves' (to the single turbine power curves),
        'wind_farm_power_curves'. Default: 'wind_farm_power_curves'.

    Other Parameters
    ----------------
    wind_speed_model : str
        Parameter to define which model to use to calculate the wind speed
        at hub height. Valid options are 'logarithmic', 'hellman' and
        'interpolation_extrapolation'.
    temperature_model : str
        Parameter to define which model to use to calculate the temperature
        of air at hub height. Valid options are 'linear_gradient' and
        'interpolation_extrapolation'.
    density_model : str
        Parameter to define which model to use to calculate the density of
        air at hub height. Valid options are 'barometric', 'ideal_gas' and
        'interpolation_extrapolation'.
    power_output_model : str
        Parameter to define which model to use to calculate the turbine
        power output. Valid options are 'power_curve' and
        'power_coefficient_curve'.
    density_correction : bool
        If the parameter is True the density corrected power curve is used
        for the calculation of the turbine power output.
    obstacle_height : float
        Height of obstacles in the surrounding area of the wind turbine in
        m. Set `obstacle_height` to zero for wide spread obstacles.
    hellman_exp : float
        The Hellman exponent, which combines the increase in wind speed due
        to stability of atmospheric conditions and surface roughness into
        one constant.

    Attributes
    ----------
    power_plant : :class:`~.wind_farm.WindFarm` or :class:`~.wind_turbine_cluster.WindTurbineCluster`
        A :class:`~.wind_farm.WindFarm` object representing the wind farm or
        a :class:`~.wind_turbine_cluster.WindTurbineCluster` object
        representing the wind turbine cluster.
    wake_losses_model : str or None
        Defines the method for taking wake losses within the farm into
        consideration. Options: None, 'power_efficiency_curve' or
        'constant_efficiency' or the name of a wind efficiency curve like
        'dena_mean'. Default: 'dena_mean'.
        Use :py:func:`~.wake_losses.get_wind_efficiency_curve` for all provided
        wind efficiency curves.
    smoothing : bool
        If True the power curves will be smoothed before or after the
        aggregation of power curves depending on `smoothing_order`.
        Default: False.
    block_width : float
        Width between the wind speeds in the sum of the equation in
        :py:func:`~.power_curves.smooth_power_curve`. Default: 0.5.
    standard_deviation_method : str
        Method for calculating the standard deviation for the Gauss
        distribution. Options: 'turbulence_intensity', 'Staffell_Pfenninger'.
        Default: 'turbulence_intensity'.
    smoothing_order : str
        Defines when the smoothing takes place if `smoothing` is True. Options:
        'turbine_power_curves' (to the single turbine power curves),
        'wind_farm_power_curves'. Default: 'wind_farm_power_curves'.
    power_output : :pandas:`pandas.Series<series>`
        Electrical power output of the wind turbine in W.
    power_curve : :pandas:`pandas.Dataframe<frame>` or None
        The calculated power curve of the wind farm.
    wind_speed_model : str
        Parameter to define which model to use to calculate the wind speed
        at hub height. Valid options are 'logarithmic', 'hellman' and
        'interpolation_extrapolation'.
    temperature_model : str
        Parameter to define which model to use to calculate the temperature
        of air at hub height. Valid options are 'linear_gradient' and
        'interpolation_extrapolation'.
    density_model : str
        Parameter to define which model to use to calculate the density of
        air at hub height. Valid options are 'barometric', 'ideal_gas' and
        'interpolation_extrapolation'.
    power_output_model : str
        Parameter to define which model to use to calculate the turbine
        power output. Valid options are 'power_curve' and
        'power_coefficient_curve'.
    density_correction : bool
        If the parameter is True the density corrected power curve is used
        for the calculation of the turbine power output.
    obstacle_height : float
        Height of obstacles in the surrounding area of the wind turbine in
        m. Set `obstacle_height` to zero for wide spread obstacles.
    hellman_exp : float
        The Hellman exponent, which combines the increase in wind speed due
        to stability of atmospheric conditions and surface roughness into
        one constant.

    """
    def __init__(self, power_plant, wake_losses_model='dena_mean',
                 smoothing=False, block_width=0.5,
                 standard_deviation_method='turbulence_intensity',
                 smoothing_order='wind_farm_power_curves', **kwargs):
        super(TurbineClusterModelChain, self).__init__(power_plant, **kwargs)

        self.power_plant = power_plant
        self.wake_losses_model = wake_losses_model
        self.smoothing = smoothing
        self.block_width = block_width
        self.standard_deviation_method = standard_deviation_method
        self.smoothing_order = smoothing_order

        self.power_curve = None
        self.power_output = None

    def assign_power_curve(self, weather_df):
        r"""
        Calculates the power curve of the wind turbine cluster.

        The power curve is aggregated from the wind farms' and wind turbines'
        power curves by using :func:`power_plant.assign_power_curve`. Depending
        on the parameters of the WindTurbineCluster power curves are smoothed
        and/or wake losses are taken into account.

        Parameters
        ----------
        weather_df : pandas.DataFrame
            DataFrame with time series for wind speed `wind_speed` in m/s, and
            roughness length `roughness_length` in m, as well as optionally
            temperature `temperature` in K, pressure `pressure` in Pa,
            density `density` in kg/m³ and turbulence intensity
            `turbulence_intensity` depending on `power_output_model`,
            `density_model` and `standard_deviation_model` chosen.
            The columns of the DataFrame are a MultiIndex where the first level
            contains the variable name (e.g. wind_speed) and the second level
            contains the height at which it applies (e.g. 10, if it was
            measured at a height of 10 m).  See documentation of
            :func:`TurbineClusterModelChain.run_model` for an example on how
            to create the weather_df DataFrame.

        Returns
        -------
        self

        """
        # Get turbulence intensity from weather if existent
        turbulence_intensity = (
            weather_df['turbulence_intensity'].values.mean() if
            'turbulence_intensity' in
            weather_df.columns.get_level_values(0) else None)
        # Assign power curve
        if (self.wake_losses_model == 'power_efficiency_curve' or
                self.wake_losses_model == 'constant_efficiency' or
                self.wake_losses_model is None):
            wake_losses_model_to_power_curve = self.wake_losses_model
            if self.wake_losses_model is None:
                logging.debug('Wake losses in wind farms are not considered.')
            else:
                logging.debug('Wake losses considered with {}.'.format(
                    self.wake_losses_model))
        else:
            logging.debug('Wake losses considered by {} wind '.format(
                self.wake_losses_model) + 'efficiency curve.')
            wake_losses_model_to_power_curve = None
        self.power_plant.assign_power_curve(
            wake_losses_model=wake_losses_model_to_power_curve,
            smoothing=self.smoothing, block_width=self.block_width,
            standard_deviation_method=self.standard_deviation_method,
            smoothing_order=self.smoothing_order,
            turbulence_intensity=turbulence_intensity)
        # Further logging messages
        if self.smoothing is None:
            logging.debug('Aggregated power curve not smoothed.')
        else:
            logging.debug('Aggregated power curve smoothed by method: ' +
                          self.standard_deviation_method)

        return self

    def run_model(self, weather_df):
        r"""
        Runs the model.

        Parameters
        ----------
        weather_df : pandas.DataFrame
            DataFrame with time series for wind speed `wind_speed` in m/s, and
            roughness length `roughness_length` in m, as well as optionally
            temperature `temperature` in K, pressure `pressure` in Pa,
            density `density` in kg/m³ and turbulence intensity
            `turbulence_intensity` depending on `power_output_model`,
            `density_model` and `standard_deviation_model` chosen.
            The columns of the DataFrame are a MultiIndex where the first level
            contains the variable name (e.g. wind_speed) and the second level
            contains the height at which it applies (e.g. 10, if it was
            measured at a height of 10 m). See below for an example on how to
            create the weather_df DataFrame.

        Returns
        -------
        self

        Examples
        ---------
        >>> import numpy as np
        >>> import pandas as pd
        >>> weather_df = pd.DataFrame(np.random.rand(2,6),
        ...                           index=pd.date_range('1/1/2012',
        ...                                               periods=2,
        ...                                               freq='H'),
        ...                           columns=[np.array(['wind_speed',
        ...                                              'wind_speed',
        ...                                              'temperature',
        ...                                              'temperature',
        ...                                              'pressure',
        ...                                              'roughness_length']),
        ...                                    np.array([10, 80, 10, 80,
        ...                                             10, 0])])
        >>> weather_df.columns.get_level_values(0)[0]
        'wind_speed'

        """

        self.assign_power_curve(weather_df)
        self.power_plant.mean_hub_height()
        wind_speed_hub = self.wind_speed_hub(weather_df)
        density_hub = (None if (self.power_output_model == 'power_curve' and
                                self.density_correction is False)
                       else self.density_hub(weather_df))
        if (self.wake_losses_model != 'power_efficiency_curve' and
                self.wake_losses_model != 'constant_efficiency' and
                self.wake_losses_model is not None):
            # Reduce wind speed with wind efficiency curve
            wind_speed_hub = wake_losses.reduce_wind_speed(
                wind_speed_hub,
                wind_efficiency_curve_name=self.wake_losses_model)
        self.power_output = self.calculate_power_output(wind_speed_hub,
                                                        density_hub)
        return self
