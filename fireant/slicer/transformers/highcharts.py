# coding: utf-8
import numpy as np
import pandas as pd

from .base import Transformer, TransformationException


def _format_data_point(value):
    if isinstance(value, pd.Timestamp):
        return int(value.asm8) // int(1e6)
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, np.int64):
        # Cannot serialize np.int64 to json
        return int(value)
    return value


class HighchartsLineTransformer(Transformer):
    """
    Transforms data frames into Highcharts format for several chart types, particularly line or bar charts.
    """

    chart_type = 'line'

    def transform(self, dataframe, display_schema):
        self._validate_dimensions(dataframe, display_schema['dimensions'])

        if isinstance(dataframe.index, pd.MultiIndex):
            dataframe = self._reorder_index_levels(dataframe, display_schema)
        has_references = isinstance(dataframe.columns, pd.MultiIndex)

        dim_ordinal = {name: ordinal
                       for ordinal, name in enumerate(dataframe.index.names)}
        dataframe = self._prepare_dataframe(dataframe, dim_ordinal, display_schema['dimensions'])

        if has_references:
            series = sum(
                [self._make_series(dataframe[level], dim_ordinal, display_schema, reference=level or None)
                 for level in dataframe.columns.levels[0]],
                []
            )

        else:
            series = self._make_series(dataframe, dim_ordinal, display_schema)

        result = {
            'chart': {'type': self.chart_type},
            'title': {'text': None},
            'xAxis': self.xaxis_options(dataframe, dim_ordinal, display_schema),
            'yAxis': self.yaxis_options(dataframe, dim_ordinal, display_schema),
            'tooltip': {'shared': True},
            'series': series
        }

        return result

    def xaxis_options(self, dataframe, dim_ordinal, display_schema):
        return {
            'type': 'datetime' if isinstance(dataframe.index, pd.DatetimeIndex) else 'linear'
        }

    def yaxis_options(self, dataframe, dim_ordinal, display_schema):
        if isinstance(dataframe.columns, pd.MultiIndex):
            num_metrics = len(dataframe.columns.levels[0])
        else:
            num_metrics = len(dataframe.columns)

        return [{
            'title': None
        }] * num_metrics

    def _reorder_index_levels(self, dataframe, display_schema):
        dimension_orders = [order
                            for key, dimension in display_schema['dimensions'].items()
                            for order in [key] + ([dimension['display_field']]
                                                  if 'display_field' in dimension
                                                  else [])]

        reordered = dataframe.reorder_levels(dataframe.index.names.index(level)
                                             for level in dimension_orders)
        return reordered

    def _make_series(self, dataframe, dim_ordinal, display_schema, reference=None):
        metrics = list(dataframe.columns.levels[0]
                       if isinstance(dataframe.columns, pd.MultiIndex)
                       else dataframe.columns)

        return [self._make_series_item(idx, item, dim_ordinal, display_schema, metrics, reference)
                for idx, item in dataframe.iteritems()]

    def _make_series_item(self, idx, item, dim_ordinal, display_schema, metrics, reference):
        return {
            'name': self._format_label(idx, dim_ordinal, display_schema, reference),
            'data': self._format_data(item),
            'yAxis': metrics.index(idx[0] if isinstance(idx, tuple) else idx),
            'dashStyle': 'Dot' if reference else 'Solid'
        }

    def _validate_dimensions(self, dataframe, dimensions):
        if not 0 < len(dimensions):
            raise TransformationException('Cannot transform %s chart.  '
                                          'At least one dimension is required.' % self.chart_type)

    @staticmethod
    def _make_categories(dataframe, dim_ordinal, display_schema):
        return None

    def _prepare_dataframe(self, dataframe, dim_ordinal, dimensions):
        # Replaces invalid values and unstacks the data frame for line charts.

        # Force all fields to be float (Safer for highcharts)
        dataframe = dataframe.astype(np.float).replace([np.inf, -np.inf], np.nan)

        # Unstack multi-indices
        if 1 < len(dimensions):
            # We need to unstack all of the dimensions here after the first dimension, which is the first dimension in
            # the dimensions list, not necessarily the one in the dataframe
            unstack_levels = list(self._unstack_levels(list(dimensions.items())[1:], dim_ordinal))
            dataframe = dataframe.unstack(level=unstack_levels)

        return dataframe

    def _format_label(self, idx, dim_ordinal, display_schema, reference):
        is_multidimensional = isinstance(idx, tuple)
        if is_multidimensional:
            metric_label = display_schema['metrics'].get(idx[0], idx[0])
        else:
            metric_label = display_schema['metrics'].get(idx, idx)

        if reference:
            metric_label += ' {reference}'.format(
                reference=display_schema['references'][reference]
            )

        if not is_multidimensional:
            return metric_label

        dimension_labels = [self._format_dimension_display(dim_ordinal, key, dimension, idx)
                            for key, dimension in list(display_schema['dimensions'].items())[1:]]
        dimension_labels = [dimension_label  # filter out the NaNs
                            for dimension_label in dimension_labels
                            if dimension_label is not np.nan]

        return (
            '{metric} ({dimensions})'.format(
                metric=metric_label,
                dimensions=', '.join(map(str, dimension_labels))
            )
            if dimension_labels
            else metric_label
        )

    @staticmethod
    def _format_dimension_display(dim_ordinal, key, dimension, idx):
        if 'display_field' in dimension:
            display_field = dimension['display_field']
            return idx[dim_ordinal[display_field]]

        dimension_value = idx[dim_ordinal[key]]
        if 'display_options' in dimension:
            dimension_value = dimension['display_options'].get(dimension_value, dimension_value)
        return dimension_value

    def _format_data(self, column):
        if isinstance(column, float):
            return [_format_data_point(column)]

        return [self._format_point(key, value)
                for key, value in column.iteritems()
                if not np.isnan(value)]

    @staticmethod
    def _format_point(x, y):
        return (_format_data_point(x), _format_data_point(y))

    def _unstack_levels(self, dimensions, dim_ordinal):
        for key, dimension in dimensions:
            yield dim_ordinal[key]

            if 'display_field' in dimension:
                yield dim_ordinal[dimension['display_field']]


class HighchartsColumnTransformer(HighchartsLineTransformer):
    chart_type = 'column'

    def _make_series_item(self, idx, item, dim_ordinal, display_schema, metrics, reference):
        return {
            'name': self._format_label(idx, dim_ordinal, display_schema, reference),
            'data': [_format_data_point(x)
                     for x in item
                     if not np.isnan(x)],
            'yAxis': metrics.index(idx[0] if isinstance(idx, tuple) else idx),
        }

    def xaxis_options(self, dataframe, dim_ordinal, display_schema):
        result = {'type': 'categorical'}

        categories = self._make_categories(dataframe, dim_ordinal, display_schema)
        if categories is not None:
            result['categories'] = categories

        return result

    def _validate_dimensions(self, dataframe, dimensions):
        if 1 < len(dimensions) and 1 < len(dataframe.columns):
            raise TransformationException('Cannot transform %s chart.  '
                                          'No more than 1 dimension or 2 dimensions '
                                          'with 1 metric are allowed.' % self.chart_type)

    def _prepare_dataframe(self, dataframe, dim_ordinal, dimensions):
        # Replaces invalid values and unstacks the data frame for line charts.

        # Force all fields to be float (Safer for highcharts)
        dataframe = dataframe.replace([np.inf, -np.inf], np.nan)

        # Unstack multi-indices
        if 1 < len(dimensions):
            unstack_levels = list(self._unstack_levels(list(dimensions.items())[1:], dim_ordinal))
            dataframe = dataframe.unstack(level=unstack_levels)

        return dataframe

    @staticmethod
    def _make_categories(dataframe, dim_ordinal, display_schema):
        if not display_schema['dimensions']:
            return None

        category_dimension = list(display_schema['dimensions'].values())[0]
        if 'display_options' in category_dimension:
            return [category_dimension['display_options'].get(dim, dim)
                    # Pandas gives both NaN or None in the index depending on whether a level was unstacked
                    if dim and not (isinstance(dim, float) and np.isnan(dim))
                    else 'Totals'
                    for dim in dataframe.index]

        if 'display_field' in category_dimension:
            display_field = category_dimension['display_field']
            return dataframe.index.get_level_values(display_field).unique().tolist()


class HighchartsBarTransformer(HighchartsColumnTransformer):
    chart_type = 'bar'
